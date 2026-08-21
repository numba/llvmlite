// neworcjit.cpp
//
// ORCv2 / LLJIT engine that behaves like MCJIT's ExecutionEngine for a
// Numba-style JIT. Targets LLVM 22.
//
// Beyond MCJIT-shaped basics this engine adds:
//
// - Content-hash symbol renaming, applied in-process by compileAndAdd.
//   - Per-symbol renaming: each non-local, non-declaration, non-preserve
//     GlobalValue's IR text is SHA-256 hashed and a 16-hex-char tag is
//     spliced into the linker name. Hashing is performed on the
//     pre-rename IR so f's hash includes the pre-rename names of g, h,
//     ... regardless of what those get renamed to in this same pass.
//   - Itanium ABI-tag insertion (`B<len><tag>`) when the original name
//     is Itanium-mangled; a `.<hex>` suffix otherwise. The ABI-tag form
//     keeps the name demangleable for tools (objdump, perf, debuggers).
// - `!numba.preserve` per-GV metadata to opt out of renaming. Reserved
//   for symbols looked up by linker name from outside the JIT
//   (NRT helpers, externals registered via ll.add_symbol).
// - `!numba.env_for` per-GV delegation: a GV's hash is the named
//   function's hash, not the GV's own body hash. Used by Numba env GVs
//   whose body is uniform (`null voidptr`); see hashGlobalValue.
// - Unified emit-then-load (compileAndAdd): emits a `.o` via the
//   engine's TargetMachine, frames it with the rename map, loads via
//   the object layer; the Python notify callback receives the framed
//   blob directly. The IRCompileLayer (and its IRMaterializationUnit
//   duplicate-symbol assertion) is bypassed. First-wins for
//   cross-module weak/linkonce_odr dups is delivered by
//   ObjectLinkingLayer's first-wins flags, set in Create().
//   `addObjectFile` handles the cache-hit fast path -- Numba's
//   `CPUCodeLibrary._unserialize` hands persisted framed blobs to it.
// - Replay-skip: both compileAndAdd and addObjectFile probe MainJD for
//   strong-linkage defs already present; on full overlap they skip the
//   underlying load (which would otherwise SIGSEGV in JITLink or return
//   DuplicateDefinition) while still firing the notify callback.
//   Mirrors MCJIT's permissive "already loaded" semantics.
// - Per-handle rename map exposed to callers (for diagnostic / cache
//   replay only; ordinary lookups go through handle-aware shims).

#include "core.h"

#include "llvm/AsmParser/Parser.h"
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/ExecutionEngine/Orc/CompileUtils.h"
#include "llvm/ExecutionEngine/Orc/Core.h"
#include "llvm/ExecutionEngine/Orc/Debugging/DebuggerSupport.h"
#include "llvm/ExecutionEngine/Orc/EPCDynamicLibrarySearchGenerator.h"
#include "llvm/ExecutionEngine/Orc/ExecutionUtils.h"
#include "llvm/ExecutionEngine/Orc/JITTargetMachineBuilder.h"
#include "llvm/ExecutionEngine/Orc/LLJIT.h"
#include "llvm/ExecutionEngine/Orc/ObjectLinkingLayer.h"
#include "llvm/IR/GlobalValue.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/Object/ObjectFile.h"
#include "llvm/Object/SymbolicFile.h"
#include "llvm/Support/Casting.h"
#include "llvm/Support/DynamicLibrary.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/SHA256.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Target/TargetMachine.h"

#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <iostream>

using namespace llvm;
using namespace llvm::orc;

using NumbaResolverFn = std::function<uint64_t(const std::string &)>;
using ModuleHandle = uint64_t;
using RenameMap = std::map<std::string, std::string>;

// Env-gated diagnostic prints. Set LLVMLITE_ORCJIT_DEBUG=1 to enable; any
// other value (or unset) disables. Computed once at first use.
static bool debugEnabled() {
  static const bool Enabled = []() {
    const char *V = std::getenv("LLVMLITE_ORCJIT_DEBUG");
    return V && V[0] == '1' && V[1] == '\0';
  }();
  return Enabled;
}
#define DEBUG debugEnabled()

//===----------------------------------------------------------------------===//
// Itanium ABI-tag insertion
//===----------------------------------------------------------------------===//

namespace {

// True if `s` looks like an Itanium-mangled name (`_Z...`). We deliberately
// do *not* try to parse the full grammar; we only need to find a safe place
// to splice in a B<len><tag> ABI-tag run.
bool isItaniumMangled(StringRef Name) { return Name.starts_with("_Z"); }

// Encode a B<len><tag> Itanium ABI tag.
std::string makeABITag(StringRef Tag) {
  std::string Out = "B";
  std::string PrefixedTag = (StringRef("_") + Tag).str();
  Out += std::to_string(PrefixedTag.size());
  Out.append(PrefixedTag.data(), PrefixedTag.size());
  return Out;
}

// Find the index in `s` (starting at offset `pos`) of the end of an Itanium
// <source-name> production: a base-10 length followed by that many bytes.
// Returns SIZE_MAX on parse failure.
size_t skipSourceName(StringRef S, size_t Pos) {
  size_t LenStart = Pos;
  while (Pos < S.size() && S[Pos] >= '0' && S[Pos] <= '9')
    ++Pos;
  if (Pos == LenStart || Pos == S.size())
    return SIZE_MAX;
  unsigned Len = 0;
  for (size_t i = LenStart; i < Pos; ++i)
    Len = Len * 10 + unsigned(S[i] - '0');
  if (Pos + Len > S.size())
    return SIZE_MAX;
  return Pos + Len;
}

// Skip any run of B<len><tag> ABI tags starting at Pos. Returns the new
// position after the last consumed tag (or Pos if none).
size_t skipABITags(StringRef S, size_t Pos) {
  while (Pos < S.size() && S[Pos] == 'B') {
    size_t End = skipSourceName(S, Pos + 1);
    if (End == SIZE_MAX)
      return Pos;
    Pos = End;
  }
  return Pos;
}

// Compute the index in a free-function mangled name `_Z<name><tags?><params>`
// where a new ABI tag must be spliced in (immediately after the existing tag
// run, i.e. between the unqualified name and the parameter type list).
//
// Free-function form ::= "_Z" <source-name> <abi-tag>* <bare-function-type>
// We only handle this shape; for nested names (`_ZN...E`) we splice before
// the terminating 'E'. Returns SIZE_MAX if we can't find a safe insertion
// point (caller should fall back to the suffix path).
size_t findItaniumInsertionPoint(StringRef S) {
  if (!S.starts_with("_Z") || S.size() < 4)
    return SIZE_MAX;
  if (S[2] == 'N') {
    // Nested name: splice immediately before the terminating 'E'. The 'E'
    // closes the nested-name production; ABI tags on the innermost
    // unqualified name go right before it. Find the last 'E' that isn't
    // inside a source-name (Itanium <source-name> can contain anything).
    // Easier: scan forward, but we have to walk source-names properly so
    // we don't mistake an 'E' inside a name for the terminator.
    size_t Pos = 3; // past "_ZN"
    size_t LastE = SIZE_MAX;
    while (Pos < S.size()) {
      char c = S[Pos];
      if (c == 'E') {
        LastE = Pos;
        ++Pos;
      } else if (c >= '0' && c <= '9') {
        size_t End = skipSourceName(S, Pos);
        if (End == SIZE_MAX)
          return SIZE_MAX;
        Pos = End;
      } else if (c == 'B') {
        size_t End = skipSourceName(S, Pos + 1);
        if (End == SIZE_MAX)
          return SIZE_MAX;
        Pos = End;
      } else {
        // Any other CV/ref qualifier, template marker, etc — stop walking
        // and use the most recent 'E' we saw.
        break;
      }
    }
    if (LastE == SIZE_MAX)
      return SIZE_MAX;
    return LastE;
  }
  // Free function: source-name then optional ABI tags then params.
  size_t Pos = skipSourceName(S, 2);
  if (Pos == SIZE_MAX)
    return SIZE_MAX;
  return skipABITags(S, Pos);
}

// Append a content-hash tag to `OldName` and return the new name.
// `HashHex` must be a non-empty identifier-charset string (we use lowercase
// hex). For Itanium-mangled inputs with no substitutions, we splice the tag
// in as a proper B<len><hex> ABI tag; otherwise we fall back to a "."
// suffix.
std::string applyHashToName(StringRef OldName, StringRef HashHex) {
  if (isItaniumMangled(OldName)) {
    size_t InsAt = findItaniumInsertionPoint(OldName);
    if (InsAt != SIZE_MAX) {
      std::string Out;
      Out.reserve(OldName.size() + 4 + HashHex.size());
      Out.append(OldName.data(), InsAt);
      Out += makeABITag(HashHex);
      Out.append(OldName.data() + InsAt, OldName.size() - InsAt);
      return Out;
    }
  }
  return (OldName + "." + HashHex).str();
}

std::string toHex(ArrayRef<uint8_t> Bytes, size_t MaxBytes) {
  static const char Digits[] = "0123456789abcdef";
  size_t N = std::min(Bytes.size(), MaxBytes);
  std::string Out;
  Out.resize(N * 2);
  for (size_t i = 0; i < N; ++i) {
    Out[2 * i] = Digits[(Bytes[i] >> 4) & 0xf];
    Out[2 * i + 1] = Digits[Bytes[i] & 0xf];
  }
  return Out;
}

} // namespace

//===----------------------------------------------------------------------===//
// Renamer pass
//===----------------------------------------------------------------------===//

namespace {

// Should we rewrite the name of this global?
//   - Declarations are references, not definitions: never rename.
//   - GVs carrying !numba.preserve are opted out by the caller.
//   - Otherwise, rename.
bool hasPreserveMD(const GlobalValue &GV) {
  if (auto *GO = dyn_cast<GlobalObject>(&GV))
    return GO->getMetadata("numba.preserve") != nullptr;
  // GlobalAlias: walk to its aliasee.
  if (auto *GA = dyn_cast<GlobalAlias>(&GV))
    if (auto *GO = dyn_cast_or_null<GlobalObject>(GA->getAliaseeObject()))
      return GO->getMetadata("numba.preserve") != nullptr;
  return false;
}

bool shouldRename(const GlobalValue &GV) {
  if (GV.isDeclaration())
    return false;
  if (hasPreserveMD(GV))
    return false;
  if (GV.getName().empty())
    return false;
  // Local-linkage GVs (internal/private) never enter the JITDylib's external
  // symbol table and never collide across modules — renaming them
  // accomplishes nothing and inflates the rename map with names that are
  // invisible to ES.lookup.
  if (GV.hasLocalLinkage())
    return false;
  return true;
}

// Hash the IR of a single GlobalValue. We print the GV (with its body) into a
// string and hash that. Because we print *before* renaming, references to
// other GVs appear under their original (possibly soon-to-be-renamed) names —
// implementing the "hash unresolved references" rule: f's hash includes the
// pre-rename name of g, regardless of what g gets renamed to.
//
// Special case — !numba.env_for delegation: a GV tagged
// `!numba.env_for !{!"<funcname>"}` adopts the named function's hash
// instead of hashing its own body. This binds the env GV's identity to its
// referencing function: same f compiled twice → same env name (legit
// cross-module sharing); different f (or different f-body) → different env
// name (no JITDylib collision). The env's own body is uniform (`null
// voidptr`) so a self-hash collapses every env GV to one name, which is
// wrong; delegation is the correct model.
//
// Name (MDString), not value reference: Numba emits the env GV before the
// function body is added to the module, so a `ptr @f` reference would
// dangle at emit time. By name, the lookup happens here in the rename pass
// when the module is final.
std::string hashGlobalValue(const GlobalValue &GV) {
  if (auto *GO = dyn_cast<GlobalObject>(&GV)) {
    if (auto *MD = GO->getMetadata("numba.env_for")) {
      if (MD->getNumOperands() >= 1) {
        if (auto *MS = dyn_cast_or_null<MDString>(MD->getOperand(0).get())) {
          if (const Module *M = GO->getParent())
            if (Function *F = M->getFunction(MS->getString()))
              return hashGlobalValue(*F);
        }
      }
    }
  }
  std::string Buf;
  raw_string_ostream OS(Buf);
  GV.print(OS);
  OS.flush();
  auto Digest = SHA256::hash(
      ArrayRef<uint8_t>(reinterpret_cast<const uint8_t *>(Buf.data()),
                        Buf.size()));
  // 8 bytes = 16 hex chars: ample collision resistance, short tags.
  return toHex(Digest, 8);
}

// Run the rename pass over `M`. Populates `Out` with old->new for every
// rewritten symbol. Modifies `M` in place.
void renameModule(Module &M, RenameMap &Out) {
  std::vector<GlobalValue *> Targets;
  for (Function &F : M)
    if (shouldRename(F))
      Targets.push_back(&F);
  for (GlobalVariable &GV : M.globals())
    if (shouldRename(GV))
      Targets.push_back(&GV);
  for (GlobalAlias &A : M.aliases())
    if (shouldRename(A))
      Targets.push_back(&A);

  // Two-phase: hash everything first (the print()-based hash sees pre-rename
  // names everywhere), then rename. setName updates intra-module uses
  // automatically.
  std::vector<std::pair<GlobalValue *, std::string>> News;
  News.reserve(Targets.size());
  for (GlobalValue *GV : Targets) {
    std::string Hex = hashGlobalValue(*GV);
    std::string Old = GV->getName().str();
    News.emplace_back(GV, applyHashToName(Old, Hex));
  }
  for (auto &P : News) {
    GlobalValue *GV = P.first;
    std::string Old = GV->getName().str();
    if (Old == P.second)
      continue;
    GV->setName(P.second);
    // setName may have uniquified by appending its own suffix if the chosen
    // name was already taken. Record what actually stuck.
    Out[Old] = GV->getName().str();
  }
}

} // namespace

//===----------------------------------------------------------------------===//
// Custom DefinitionGenerator: Numba's lazy resolver.
//===----------------------------------------------------------------------===//

class NumbaSymbolGenerator : public DefinitionGenerator {
public:
  explicit NumbaSymbolGenerator(NumbaResolverFn Resolve)
      : Resolve(std::move(Resolve)) {}

  Error tryToGenerate(LookupState &LS, LookupKind K, JITDylib &JD,
                      JITDylibLookupFlags JDLookupFlags,
                      const SymbolLookupSet &LookupSet) override {
    SymbolMap NewDefs;
    for (const auto &KV : LookupSet) {
      const SymbolStringPtr &Name = KV.first;
      uint64_t Addr = Resolve((*Name).str());
      if (!Addr) {
        if (DEBUG)
          std::cerr << "**** [NumbaSymbolGenerator] Unable to resolve name: " << (*Name).str() << std::endl;
      }
      if (Addr) {
        NewDefs[Name] =
            ExecutorSymbolDef(ExecutorAddr(Addr), JITSymbolFlags::Exported);
      } else {
        if (DEBUG)
          std::cerr << "****** [NumbaSymbolGenerator] STILL Unable to resolve name: " << (*Name).str() << std::endl;
      }
    }
    if (NewDefs.empty())
      return Error::success();
    return JD.define(absoluteSymbols(std::move(NewDefs)));
  }

private:
  NumbaResolverFn Resolve;
};


class LLVMAddSymbolResolver : public DefinitionGenerator {
public:
  Error tryToGenerate(LookupState &LS, LookupKind K, JITDylib &JD,
                      JITDylibLookupFlags JDLookupFlags,
                      const SymbolLookupSet &LookupSet) override {
    SymbolMap NewDefs;
    for (const auto &KV : LookupSet) {
      const SymbolStringPtr &Name = KV.first;
      uint64_t Addr = 0;
      if (DEBUG)
        std::cerr << "****[LLVMAddSymbolResolver] resolving: " << (*Name).str() << std::endl;
      if (void *P = llvm::sys::DynamicLibrary::SearchForAddressOfSymbol(
                (*Name).str().c_str())) {
        Addr = reinterpret_cast<uint64_t>(P);
        NewDefs[Name] =
            ExecutorSymbolDef(ExecutorAddr(Addr), JITSymbolFlags::Exported);
      } else {
        if (DEBUG)
          std::cerr << "****[LLVMAddSymbolResolver] Unable to resolve name: " << (*Name).str() << std::endl;
      }
    }
    if (NewDefs.empty())
      return Error::success();
    return JD.define(absoluteSymbols(std::move(NewDefs)));
  }

};

//===----------------------------------------------------------------------===//
// Callback-driven ObjectCache
//===----------------------------------------------------------------------===//

// Python (or any caller) installs this function pointer; compileAndAdd
// invokes it after a successful addObjectFile with the framed blob.
// *Key* is the LLVM Module identifier — the caller is responsible for
// setting it to whatever cache key they want before adding the module.
typedef void (*ObjCacheNotifyFn)(const char *Key, const char *Bytes,
                                 size_t Len);

// Forward decl: the engine owns the rename-map side-table that the framed
// cache layer consults.
class OrcEngine;

// Framed-blob format for the on-disk cache. We bundle the per-handle rename
// map alongside the LLVM-emitted object bytes so cache-hit consumers don't
// have to manage two parallel persisted artifacts.
//
//   bytes[0..3]   : magic        = "NORC"
//   bytes[4]      : version      = 0x01
//   bytes[5..8]   : u32 little-endian rename-map byte length (RM_LEN)
//   bytes[9..9+RM_LEN)            : rename-map payload (alternating
//                                   null-terminated old/new pairs, same
//                                   encoding as LLVMPY_NewOrcJIT_GetRenameMap)
//   bytes[9+RM_LEN..]             : object-file bytes
//
// On parse we tolerate legacy raw object bytes (no magic) so old caches keep
// working; bad-version is a hard error.
static constexpr char kFrameMagic[4] = {'N', 'O', 'R', 'C'};
static constexpr uint8_t kFrameVersion = 0x01;
static constexpr size_t kFrameHeaderLen = 4 + 1 + 4;

// Serialize a RenameMap into the alternating null-terminated form.
static std::string serializeRenameMap(const RenameMap &M) {
  std::string Out;
  for (auto &P : M) {
    Out.append(P.first.data(), P.first.size());
    Out.push_back('\0');
    Out.append(P.second.data(), P.second.size());
    Out.push_back('\0');
  }
  return Out;
}

static RenameMap deserializeRenameMap(StringRef Buf) {
  RenameMap M;
  size_t i = 0;
  while (i < Buf.size()) {
    const char *Old = Buf.data() + i;
    size_t OldLen = strnlen(Old, Buf.size() - i);
    i += OldLen + 1;
    if (i > Buf.size())
      break;
    const char *New = Buf.data() + i;
    size_t NewLen = strnlen(New, Buf.size() - i);
    i += NewLen + 1;
    M[std::string(Old, OldLen)] = std::string(New, NewLen);
  }
  return M;
}

// Build a framed blob from a rename map + raw object bytes.
static std::string frameBlob(const RenameMap &RM, StringRef ObjBytes) {
  std::string RMBytes = serializeRenameMap(RM);
  std::string Out;
  Out.reserve(kFrameHeaderLen + RMBytes.size() + ObjBytes.size());
  Out.append(kFrameMagic, 4);
  Out.push_back(static_cast<char>(kFrameVersion));
  uint32_t Len = static_cast<uint32_t>(RMBytes.size());
  // little-endian u32
  Out.push_back(static_cast<char>(Len & 0xff));
  Out.push_back(static_cast<char>((Len >> 8) & 0xff));
  Out.push_back(static_cast<char>((Len >> 16) & 0xff));
  Out.push_back(static_cast<char>((Len >> 24) & 0xff));
  Out.append(RMBytes);
  Out.append(ObjBytes.data(), ObjBytes.size());
  return Out;
}

// Parse a framed blob into (rename-map, inner object bytes).
// Returns success with HasFrame=false if the blob lacks our magic — the
// caller treats it as legacy raw object bytes (no rename map).
struct ParsedFrame {
  bool HasFrame;
  RenameMap RM;
  StringRef ObjBytes;
};

static Expected<ParsedFrame> parseFrame(StringRef Blob) {
  ParsedFrame P{false, {}, Blob};
  if (Blob.size() < kFrameHeaderLen ||
      std::memcmp(Blob.data(), kFrameMagic, 4) != 0) {
    // Legacy / unframed: hand back whole blob as object bytes.
    return P;
  }
  uint8_t Ver = static_cast<uint8_t>(Blob[4]);
  if (Ver != kFrameVersion) {
    return make_error<StringError>(
        "neworcjit: unsupported framed-cache version",
        inconvertibleErrorCode());
  }
  uint32_t RMLen = static_cast<uint8_t>(Blob[5]) |
                   (static_cast<uint32_t>(static_cast<uint8_t>(Blob[6])) << 8) |
                   (static_cast<uint32_t>(static_cast<uint8_t>(Blob[7])) << 16) |
                   (static_cast<uint32_t>(static_cast<uint8_t>(Blob[8])) << 24);
  if (kFrameHeaderLen + RMLen > Blob.size()) {
    return make_error<StringError>(
        "neworcjit: framed-cache rename-map length out of range",
        inconvertibleErrorCode());
  }
  P.HasFrame = true;
  P.RM = deserializeRenameMap(Blob.substr(kFrameHeaderLen, RMLen));
  P.ObjBytes = Blob.substr(kFrameHeaderLen + RMLen);
  return P;
}

// Holds the Python-side notify callback. The engine no longer routes
// anything through ORC's IRCompileLayer, so the LLVM ObjectCache interface
// (notifyObjectCompiled + getObject) was deleted. compileAndAdd invokes
// this trampoline directly after addObjectFile succeeds, handing it the
// already-framed blob. Numba's CPUCodeLibrary._on_object_compiled captures
// the bytes from there for on-disk persistence.
class CallbackObjectCache {
public:
  CallbackObjectCache(ObjCacheNotifyFn N) : Notify(N) {}

  void notifyFramed(StringRef ModID, StringRef Framed) {
    if (!Notify)
      return;
    std::lock_guard<std::mutex> L(Mu);
    Notify(ModID.str().c_str(), Framed.data(), Framed.size());
  }

private:
  ObjCacheNotifyFn Notify;
  std::mutex Mu;
};

//===----------------------------------------------------------------------===//
// The engine
//===----------------------------------------------------------------------===//

class OrcEngine {
public:
  static Expected<std::unique_ptr<OrcEngine>> Create(NumbaResolverFn Resolver,
                                                     bool UseProcessSymbols) {
    auto JTMB = JITTargetMachineBuilder::detectHost();
    if (!JTMB)
      return JTMB.takeError();

    // Build a standalone TargetMachine for compile_and_add's emit_object
    // path. ConcurrentIRCompiler builds its own TM per thread; this one is
    // for our direct codegen path. Numba holds the global compiler lock so
    // single-threaded use is fine.
    auto TMOrErr = JTMB->createTargetMachine();
    if (!TMOrErr)
      return TMOrErr.takeError();

    LLJITBuilder Builder;
    Builder.setJITTargetMachineBuilder(std::move(*JTMB));
    Builder.setPrePlatformSetup([](LLJIT &J) {
      consumeError(enableDebuggerSupport(J));
      return Error::success();
    });

    auto JIT = Builder.create();
    if (!JIT)
      return JIT.takeError();

    auto Eng = std::unique_ptr<OrcEngine>(new OrcEngine(std::move(*JIT)));
    Eng->TM = std::move(*TMOrErr);

    // ODR-merge flags. Belt-and-braces with content-hash naming, but cheap.
    if (auto *OLL = dyn_cast<ObjectLinkingLayer>(
            &Eng->JIT->getObjLinkingLayer())) {
      OLL->setOverrideObjectFlagsWithResponsibilityFlags(true);
      OLL->setAutoClaimResponsibilityForObjectSymbols(true);
    }

    // Process / dylib generators live on the ProcessSymbols dylib (clang-repl
    // pattern); main holds *defined* symbols only.
    JITDylibSP ProcJD = Eng->JIT->getProcessSymbolsJITDylib();
    if (!ProcJD)
      return make_error<StringError>("no ProcessSymbols JITDylib",
                                     inconvertibleErrorCode());
    auto ProcGen = EPCDynamicLibrarySearchGenerator::GetForTargetProcess(
        Eng->JIT->getExecutionSession());
    if (!ProcGen)
      return ProcGen.takeError();
    ProcJD->addGenerator(std::move(*ProcGen));
      
    
    JITDylib &MainJD = Eng->JIT->getMainJITDylib();
    MainJD.addGenerator(
        std::make_unique<NumbaSymbolGenerator>(std::move(Resolver)));
    if (UseProcessSymbols) {
      if (DEBUG) std::cerr << "---- Installed LLVMAddSymbolResolver\n";
      MainJD.addGenerator(std::make_unique<LLVMAddSymbolResolver>());
    }
    return Eng;
  }

  // Unified emit-then-load entrypoint. Renames *M* in place,
  // emits a .o via the engine's TargetMachine, frames it with the rename
  // map, loads the object into the main JITDylib, and returns both the
  // handle and the framed blob so the caller can persist it directly
  // (no ObjectCache notify/get round-trip).
  //
  // First-wins for duplicate linkonce_odr defs across .o's is delivered by
  // ObjectLinkingLayer's setOverrideObjectFlagsWithResponsibilityFlags +
  // setAutoClaimResponsibilityForObjectSymbols (already wired in Create).
  // No demote pass needed: the IR-side IRMaterializationUnit duplicate
  // assertion is the only thing that required it, and we don't use the IR
  // layer here.
  Expected<std::pair<ModuleHandle, std::string>>
  compileAndAdd(std::unique_ptr<Module> M, std::unique_ptr<LLVMContext> Ctx) {
    JITDylib &JD = JIT->getMainJITDylib();
    ModuleHandle H = nextHandle();

    // Ensure the module's data layout matches our TargetMachine — the
    // codegen pass asserts on mismatch. Numba's _create_empty_module
    // already populates this; setting unconditionally is harmless.
    M->setDataLayout(TM->createDataLayout());

    RenameMap RM;
    renameModule(*M, RM);

    // Snapshot post-rename defined names for finalizeObject's eager
    // materialization. Also collect strong-linkage defs for the replay-skip
    // probe below.
    std::vector<std::string> DefNames;
    std::vector<std::string> StrongDefs;
    auto collect = [&](const GlobalValue &GV) {
      DefNames.push_back(GV.getName().str());
      if (!GV.isWeakForLinker())
        StrongDefs.push_back(GV.getName().str());
    };
    for (Function &F : *M)
      if (!F.isDeclaration() && !F.hasLocalLinkage() && !F.getName().empty())
        collect(F);
    for (GlobalVariable &GV : M->globals())
      if (!GV.isDeclaration() && !GV.hasLocalLinkage() && !GV.getName().empty())
        collect(GV);

    std::string ModID = M->getModuleIdentifier();

    // Replay-skip probe: same shape as addObjectFile's path. When
    // forceobj + looplift re-emits a module with identical content (or any
    // caller hands us the same IR twice), every strong def hashes to the
    // same renamed name and is already published. The underlying
    // JIT->addObjectFile would SIGSEGV inside JITLink rather than return a
    // DuplicateDefinition error.
    //
    // We still need to *emit* and fire the notify callback below: Numba's
    // CPUCodeLibrary captures the framed blob via the notify trampoline
    // (_on_object_compiled) and would fail to serialize itself to disk
    // without one. Only the JIT->addObjectFile load step is skipped.
    //
    // Weak/linkonce_odr duplicates are intentionally not probed — the
    // ObjectLinkingLayer first-wins flags handle those silently, and
    // probing them would mark any object whose helpers were inlined
    // elsewhere as a spurious replay.
    bool ReplaySkip = false;
    if (!StrongDefs.empty()) {
      auto &ES = JIT->getExecutionSession();
      SymbolLookupSet Probe;
      for (const std::string &N : StrongDefs)
        Probe.add(ES.intern(N), SymbolLookupFlags::WeaklyReferencedSymbol);
      auto Found = ES.lookupFlags(
          LookupKind::Static,
          makeJITDylibSearchOrder(&JD,
                                  JITDylibLookupFlags::MatchAllSymbols),
          Probe);
      if (!Found)
        return Found.takeError();
      ReplaySkip = (Found->size() == StrongDefs.size());
    }

    // Emit .o into a SmallVector, then transfer to a stable string.
    SmallVector<char, 0> ObjBuf;
    {
      raw_svector_ostream OS(ObjBuf);
      legacy::PassManager PM;
      if (TM->addPassesToEmitFile(PM, OS, /*DwoOut=*/nullptr,
                                  CodeGenFileType::ObjectFile)) {
        return make_error<StringError>(
            "neworcjit: TargetMachine cannot emit object file",
            inconvertibleErrorCode());
      }
      PM.run(*M);
    }
    std::string ObjBytes(ObjBuf.begin(), ObjBuf.end());
    std::string Framed = frameBlob(RM, ObjBytes);

    ResourceTrackerSP RT = JD.createResourceTracker();
    if (!ReplaySkip) {
      auto Buf = MemoryBuffer::getMemBufferCopy(
          StringRef(ObjBytes.data(), ObjBytes.size()), ModID);
      if (Error Err = JIT->addObjectFile(RT, std::move(Buf))) {
        consumeError(RT->remove());
        return std::move(Err);
      }
    }
    if (!RM.empty()) {
      std::lock_guard<std::mutex> L(RenameMu);
      RenameMaps[H] = std::move(RM);
    }
    {
      std::lock_guard<std::mutex> L(ModIDMu);
      if (!ModID.empty())
        ModIDToHandle[ModID] = H;
    }
    {
      std::lock_guard<std::mutex> L(TrackersMu);
      Trackers[H] = std::move(RT);
      // ReplaySkip: stash empty DefinedNames so finalizeObject doesn't
      // re-materialize already-published symbols through this handle.
      DefinedNames[H] = ReplaySkip ? std::vector<std::string>{}
                                   : std::move(DefNames);
    }
    // Fire the Python-side notify callback (Numba's
    // CPUCodeLibrary._on_object_compiled path) with the already-framed
    // blob. Replaces the dead IR-layer ObjectCache notifyObjectCompiled
    // hook.
    if (Cache_)
      Cache_->notifyFramed(ModID, Framed);
    // Explicit ordering: Module references its Context, so destroy Module
    // first. C++ argument destruction order is unspecified; without these
    // explicit resets we can SIGSEGV in ~Module() walking freed Context
    // bookkeeping.
    M.reset();
    Ctx.reset();
    return std::make_pair(H, std::move(Framed));
  }

  // Add an object file. *Blob* may be a framed blob (NORC magic, with
  // bundled rename map) or raw object bytes. The rename map, if present,
  // is installed on the returned handle automatically — callers do not
  // need to call setRenameMap themselves.
  Expected<ModuleHandle>
  addObjectFile(StringRef Blob, StringRef Name) {
    auto Parsed = parseFrame(Blob);
    if (!Parsed)
      return Parsed.takeError();

    auto Buf = MemoryBuffer::getMemBufferCopy(Parsed->ObjBytes, Name);

    JITDylib &JD = JIT->getMainJITDylib();
    ResourceTrackerSP RT = JD.createResourceTracker();
    ModuleHandle H = nextHandle();
    if (Parsed->HasFrame && !Parsed->RM.empty()) {
      std::lock_guard<std::mutex> L(RenameMu);
      RenameMaps[H] = Parsed->RM;
    }

    // Snapshot the globally-visible defined symbols from the object file
    // itself so finalize_object's eager materialization (ES.lookup) only
    // touches names that actually live in the JITDylib's external symbol
    // table. The rename map can't substitute: preserve-tagged externals
    // (NRT helpers, etc.) are excluded from renaming and so absent from
    // the map, while a .o symbol-table walk catches them.
    std::vector<std::string> DefNames;
    std::vector<std::string> StrongDefs;
    {
      auto ObjOrErr = object::ObjectFile::createObjectFile(
          Buf->getMemBufferRef());
      if (!ObjOrErr) {
        consumeError(RT->remove());
        {
          std::lock_guard<std::mutex> L(RenameMu);
          RenameMaps.erase(H);
        }
        return ObjOrErr.takeError();
      }
      for (auto &Sym : (*ObjOrErr)->symbols()) {
        auto FlagsOrErr = Sym.getFlags();
        if (!FlagsOrErr) {
          consumeError(FlagsOrErr.takeError());
          continue;
        }
        uint32_t F = *FlagsOrErr;
        // Keep only symbols that the loader will publish to the JITDylib's
        // external table — i.e., what a future ES.lookup can actually find.
        //   SF_Global   = ELF STB_GLOBAL/STB_WEAK (or platform analog).
        //                 Locals (STB_LOCAL: `.const.*` strings, pickle
        //                 blobs) stay confined to intra-object relocations
        //                 and never enter the JITDylib symbol table.
        //   SF_Undefined = symbol is referenced but not defined here
        //                  (extern decls — NRT helpers, libc, etc.).
        //                  These get satisfied by other JITDylib entries
        //                  or generators; this .o doesn't define them, so
        //                  they don't belong in *our* DefinedNames[H].
        if (!(F & object::BasicSymbolRef::SF_Global))
          continue;
        if (F & object::BasicSymbolRef::SF_Undefined)
          continue;
        auto NameOrErr = Sym.getName();
        if (!NameOrErr) {
          consumeError(NameOrErr.takeError());
          continue;
        }
        if (NameOrErr->empty())
          continue;
        DefNames.push_back(NameOrErr->str());
        if (!(F & object::BasicSymbolRef::SF_Weak))
          StrongDefs.push_back(NameOrErr->str());
      }
    }

    // Replay-skip: if every strong-linkage defined symbol in this .o is
    // already published in the JITDylib, treat the add as a no-op. Matches
    // MCJIT's permissive "already loaded, fine" semantics and avoids
    // DuplicateDefinition errors when a cached library is reloaded into an
    // engine that already holds its symbols (e.g. shared-cache scenarios
    // where two dispatchers resolve to the same on-disk .o).
    //
    // Detection is strong-only: weak/linkonce_odr duplicates are already
    // handled by ObjectLinkingLayer first-wins, so probing them would mark
    // an object as duplicate just because a prior .o happened to inline
    // the same helper. Strong defs are the unambiguous signal.
    if (!StrongDefs.empty()) {
      auto &ES = JIT->getExecutionSession();
      SymbolLookupSet Probe;
      for (const std::string &N : StrongDefs)
        Probe.add(ES.intern(N), SymbolLookupFlags::WeaklyReferencedSymbol);
      auto Found = ES.lookupFlags(
          LookupKind::Static,
          makeJITDylibSearchOrder(&JD,
                                  JITDylibLookupFlags::MatchAllSymbols),
          Probe);
      if (!Found) {
        consumeError(RT->remove());
        {
          std::lock_guard<std::mutex> L(RenameMu);
          RenameMaps.erase(H);
        }
        return Found.takeError();
      }
      if (Found->size() == StrongDefs.size()) {
        // All strong defs already present — skip the actual load. Keep the
        // rename map (so per-handle name translation still works) but stash
        // an empty DefinedNames[H] so finalize_object doesn't try to
        // re-materialize anything via this handle. Keep RT live so
        // removeModule(H) remains well-defined (its remove() is a no-op
        // since nothing was added under it).
        std::lock_guard<std::mutex> L(TrackersMu);
        Trackers[H] = std::move(RT);
        DefinedNames[H] = {};
        return H;
      }
      // Partial overlap is unexpected; fall through and let
      // JIT->addObjectFile surface the DuplicateDefinition.
    }

    if (Error Err = JIT->addObjectFile(RT, std::move(Buf))) {
      consumeError(RT->remove());
      {
        std::lock_guard<std::mutex> L(RenameMu);
        RenameMaps.erase(H);
      }
      return std::move(Err);
    }
    {
      std::lock_guard<std::mutex> L(TrackersMu);
      Trackers[H] = std::move(RT);
      DefinedNames[H] = std::move(DefNames);
    }
    return H;
  }

  Error removeModule(ModuleHandle H) {
    ResourceTrackerSP RT;
    {
      std::lock_guard<std::mutex> L(TrackersMu);
      auto It = Trackers.find(H);
      if (It == Trackers.end())
        return make_error<StringError>("unknown module handle",
                                       inconvertibleErrorCode());
      RT = std::move(It->second);
      Trackers.erase(It);
      DefinedNames.erase(H);
    }
    {
      std::lock_guard<std::mutex> L(RenameMu);
      RenameMaps.erase(H);
    }
    {
      std::lock_guard<std::mutex> L(ModIDMu);
      for (auto It = ModIDToHandle.begin(); It != ModIDToHandle.end();) {
        if (It->second == H)
          It = ModIDToHandle.erase(It);
        else
          ++It;
      }
    }
    return RT->remove();
  }

  Error addGlobalMapping(StringRef UnmangledName, void *Addr) {
    JITDylib &JD = JIT->getMainJITDylib();
    SymbolMap M;
    M[JIT->mangleAndIntern(UnmangledName)] =
        ExecutorSymbolDef(ExecutorAddr::fromPtr(Addr), JITSymbolFlags::Exported);
    return JD.define(absoluteSymbols(std::move(M)));
  }

  Error loadDynamicLibrary(StringRef Path) {
    JITDylibSP ProcJD = JIT->getProcessSymbolsJITDylib();
    if (!ProcJD)
      return make_error<StringError>("no ProcessSymbols JITDylib",
                                     inconvertibleErrorCode());
    auto Gen = EPCDynamicLibrarySearchGenerator::Load(
        JIT->getExecutionSession(), Path.str().c_str());
    if (!Gen)
      return Gen.takeError();
    ProcJD->addGenerator(std::move(*Gen));
    return Error::success();
  }

  Expected<uint64_t> getFunctionAddress(StringRef Name) {
    auto Sym = JIT->lookup(Name);
    if (!Sym)
      return Sym.takeError();
    return Sym->getValue();
  }

  Expected<uint64_t> getLinkerSymbolAddress(StringRef Name) {
    auto &ES = JIT->getExecutionSession();
    auto Sym = ES.lookup(makeJITDylibSearchOrder(&JIT->getMainJITDylib()),
                         ES.intern(Name));
    if (!Sym)
      return Sym.takeError();
    return Sym->getAddress().getValue();
  }

  // Non-materializing existence check against the main JITDylib.
  // Treats *LinkerName* as already-mangled (caller resolved any per-handle
  // rename mapping before calling).
  bool isSymbolDefined(StringRef LinkerName) {
    auto &ES = JIT->getExecutionSession();
    JITDylib &JD = JIT->getMainJITDylib();
    auto Sym = ES.intern(LinkerName);
    SymbolLookupSet Set;
    Set.add(Sym, SymbolLookupFlags::WeaklyReferencedSymbol);
    auto Result = ES.lookupFlags(
        LookupKind::Static,
        makeJITDylibSearchOrder(&JD,
                                JITDylibLookupFlags::MatchAllSymbols),
        Set);
    if (!Result) {
      consumeError(Result.takeError());
      return false;
    }
    return Result->count(Sym) > 0;
  }

  std::string getDataLayoutString() {
    return JIT->getDataLayout().getStringRepresentation();
  }

  // Eager finalize: force materialization of every defined symbol on every
  // live handle, surfacing codegen errors here rather than at first call.
  // Mirrors MCJIT's finalizeObject() semantics.
  Error finalizeObject() {
    auto &ES = JIT->getExecutionSession();
    JITDylib &JD = JIT->getMainJITDylib();

    SymbolLookupSet Set;
    {
      std::lock_guard<std::mutex> L(TrackersMu);
      // Dedup across handles: the same weak/linkonce_odr symbol can
      // appear in multiple handles' DefinedNames. With Numba's helper-
      // library inlining (CPUCodeLibrary.finalize link_in + inliner),
      // identical helper closures land in many user libraries' .o's,
      // each registered as a separate handle here. ES.lookup builds an
      // internal dependence map keyed by symbol name and asserts on
      // duplicate dependence notifications.
      std::unordered_set<std::string> Seen;
      for (auto &KV : DefinedNames) {
        for (const std::string &N : KV.second) {
          if (Seen.insert(N).second)
            Set.add(ES.intern(N));
        }
      }
    }
    if (!Set.empty()) {
      auto Sym = ES.lookup(makeJITDylibSearchOrder(&JD), Set);
      if (!Sym)
        return Sym.takeError();
    }
    return JIT->initialize(JD);
  }
  Error runStaticDestructors() {
    return JIT->deinitialize(JIT->getMainJITDylib());
  }

  RenameMap getRenameMap(ModuleHandle H) {
    std::lock_guard<std::mutex> L(RenameMu);
    auto It = RenameMaps.find(H);
    if (It == RenameMaps.end())
      return {};
    return It->second;
  }

  void setRenameMap(ModuleHandle H, RenameMap M) {
    std::lock_guard<std::mutex> L(RenameMu);
    RenameMaps[H] = std::move(M);
  }

  // Install/replace the framed-blob notify trampoline. compileAndAdd fires
  // it after each successful addObjectFile so Numba's _on_object_compiled
  // sees freshly produced blobs and stores them on disk.
  void setObjectCache(std::unique_ptr<CallbackObjectCache> Cache) {
    Cache_ = std::move(Cache);
  }

  // Parse textual IR into a fresh module + context, hand to compileAndAdd.
  // Returns 0 on parse failure (ErrMsg populated) or 0 with empty handle/blob
  // on emit failure.
  ModuleHandle parseAndCompileAndAdd(StringRef IR, StringRef ModID,
                                     std::string &ErrMsg,
                                     std::string &OutBlob) {
    auto Ctx = std::make_unique<LLVMContext>();
    SMDiagnostic Err;
    auto MemBuf = MemoryBuffer::getMemBuffer(IR, "<jit-ir>");
    auto M = parseAssembly(MemBuf->getMemBufferRef(), Err, *Ctx);
    if (!M) {
      ErrMsg = Err.getMessage().str();
      return 0;
    }
    if (!ModID.empty())
      M->setModuleIdentifier(ModID);
    auto R = compileAndAdd(std::move(M), std::move(Ctx));
    if (!R) {
      ErrMsg = toString(R.takeError());
      return 0;
    }
    OutBlob = std::move(R->second);
    return R->first;
  }

private:
  explicit OrcEngine(std::unique_ptr<LLJIT> J) : JIT(std::move(J)) {}

  ModuleHandle nextHandle() { return ++NextHandle; }

  std::unique_ptr<LLJIT> JIT;
  std::atomic<ModuleHandle> NextHandle{0};

  std::mutex TrackersMu;
  std::map<ModuleHandle, ResourceTrackerSP> Trackers;
  // Linker-mangled names of every globally-visible defined symbol on
  // each handle. compileAndAdd populates from the post-rename IR;
  // addObjectFile populates from the object-file symtab walk (which
  // also picks up preserve-tagged externals not in the rename map).
  // Replay-skip handles get an empty vector — their defs are already
  // owned by a previous handle, so eager finalize must not touch them
  // here. Used only by finalizeObject().
  std::map<ModuleHandle, std::vector<std::string>> DefinedNames;

  std::mutex RenameMu;
  std::map<ModuleHandle, RenameMap> RenameMaps;

  std::mutex ModIDMu;
  std::map<std::string, ModuleHandle> ModIDToHandle;

  std::unique_ptr<CallbackObjectCache> Cache_;
  std::unique_ptr<TargetMachine> TM;
};

//===----------------------------------------------------------------------===//
// C bindings
//===----------------------------------------------------------------------===//

namespace {

typedef uint64_t (*NumbaResolverCallback)(const char *Name);

NumbaResolverFn makeResolverFn(NumbaResolverCallback CB) {
  if (!CB)
    return [](const std::string &) -> uint64_t { return 0; };
  return [CB](const std::string &Name) -> uint64_t { return CB(Name.c_str()); };
}

} // namespace

extern "C" {

API_EXPORT(OrcEngine *)
LLVMPY_NewOrcJIT_Create(NumbaResolverCallback Resolver,
                        int UseProcessSymbols,
                        const char **OutError) {
  auto Eng = OrcEngine::Create(makeResolverFn(Resolver),
                               UseProcessSymbols != 0);
  if (!Eng) {
    *OutError = LLVMPY_CreateString(toString(Eng.takeError()).c_str());
    return nullptr;
  }
  return (*Eng).release();
}

API_EXPORT(void)
LLVMPY_NewOrcJIT_Dispose(OrcEngine *Eng) { delete Eng; }

// Unified entrypoint. Parses *IR*, runs the rename pass, emits
// the .o, frames it with the rename map, loads via addObjectFile. On
// success returns the handle and writes the framed blob bytes to
// (*OutBlob, *OutBlobLen) — caller must free *OutBlob via
// LLVMPY_DisposeString.
API_EXPORT(uint64_t)
LLVMPY_NewOrcJIT_CompileAndAdd(OrcEngine *Eng, const char *IR,
                               const char *ModID,
                               char **OutBlob, size_t *OutBlobLen,
                               const char **OutError) {
  std::string ErrMsg;
  std::string Blob;
  ModuleHandle H =
      Eng->parseAndCompileAndAdd(IR, ModID ? ModID : "", ErrMsg, Blob);
  if (H == 0) {
    *OutError = LLVMPY_CreateString(ErrMsg.c_str());
    *OutBlob = nullptr;
    *OutBlobLen = 0;
    return 0;
  }
  char *Buf = static_cast<char *>(malloc(Blob.size()));
  std::memcpy(Buf, Blob.data(), Blob.size());
  *OutBlob = Buf;
  *OutBlobLen = Blob.size();
  return H;
}

// Thin alias for CompileAndAdd that discards the framed blob. The Python
// binding's add_ir_module still routes here for code paths that don't
// need the blob in-hand (Numba's notify callback captures it instead).
API_EXPORT(uint64_t)
LLVMPY_NewOrcJIT_AddIRModule(OrcEngine *Eng, const char *IR,
                             const char *ModID, const char **OutError) {
  std::string ErrMsg;
  std::string Blob;  // discarded
  ModuleHandle H =
      Eng->parseAndCompileAndAdd(IR, ModID ? ModID : "", ErrMsg, Blob);
  if (H == 0) {
    *OutError = LLVMPY_CreateString(ErrMsg.c_str());
    return 0;
  }
  return H;
}

API_EXPORT(uint64_t)
LLVMPY_NewOrcJIT_AddObjectFile(OrcEngine *Eng, const char *Bytes, size_t Len,
                               const char *Name, const char **OutError) {
  auto H = Eng->addObjectFile(StringRef(Bytes, Len),
                              Name ? Name : "<jit-obj>");
  if (!H) {
    *OutError = LLVMPY_CreateString(toString(H.takeError()).c_str());
    return 0;
  }
  return *H;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_RemoveModule(OrcEngine *Eng, uint64_t H,
                              const char **OutError) {
  if (Error E = Eng->removeModule(H)) {
    *OutError = LLVMPY_CreateString(toString(std::move(E)).c_str());
    return 1;
  }
  return 0;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_AddGlobalMapping(OrcEngine *Eng, const char *Name,
                                  uint64_t Addr, const char **OutError) {
  if (Error E = Eng->addGlobalMapping(Name, reinterpret_cast<void *>(Addr))) {
    *OutError = LLVMPY_CreateString(toString(std::move(E)).c_str());
    return 1;
  }
  return 0;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_IsSymbolDefined(OrcEngine *Eng, const char *Name) {
  return Eng->isSymbolDefined(Name) ? 1 : 0;
}

API_EXPORT(const char *)
LLVMPY_NewOrcJIT_GetDataLayoutString(OrcEngine *Eng) {
  return LLVMPY_CreateString(Eng->getDataLayoutString().c_str());
}

API_EXPORT(uint64_t)
LLVMPY_NewOrcJIT_GetFunctionAddress(OrcEngine *Eng, const char *Name,
                                    int LinkerName, const char **OutError) {
  auto Addr = LinkerName ? Eng->getLinkerSymbolAddress(Name)
                         : Eng->getFunctionAddress(Name);
  if (!Addr) {
    *OutError = LLVMPY_CreateString(toString(Addr.takeError()).c_str());
    return 0;
  }
  return *Addr;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_LoadDynamicLibrary(OrcEngine *Eng, const char *Path,
                                    const char **OutError) {
  if (Error E = Eng->loadDynamicLibrary(Path)) {
    *OutError = LLVMPY_CreateString(toString(std::move(E)).c_str());
    return 1;
  }
  return 0;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_Finalize(OrcEngine *Eng, const char **OutError) {
  if (Error E = Eng->finalizeObject()) {
    *OutError = LLVMPY_CreateString(toString(std::move(E)).c_str());
    return 1;
  }
  return 0;
}

API_EXPORT(int)
LLVMPY_NewOrcJIT_RunStaticDestructors(OrcEngine *Eng, const char **OutError) {
  if (Error E = Eng->runStaticDestructors()) {
    *OutError = LLVMPY_CreateString(toString(std::move(E)).c_str());
    return 1;
  }
  return 0;
}

// Return
// Output buffer format: alternating null-terminated old/new pairs; total
// length in *OutLen (in bytes including all terminators). Caller frees with
// LLVMPY_DisposeString. Empty map -> *OutLen=0.
API_EXPORT(void)
LLVMPY_NewOrcJIT_GetRenameMap(OrcEngine *Eng, uint64_t H, char **OutPtrBuf, size_t *OutLen) {
  RenameMap M = Eng->getRenameMap(H);
  if (M.empty()) {
    *OutLen = 0;
    *OutPtrBuf = 0;
    return;
  }
  size_t Total = 0;
  for (auto &P : M)
    Total += P.first.size() + 1 + P.second.size() + 1;
  char *Buf = static_cast<char *>(malloc(Total));
  size_t O = 0;
  for (auto &P : M) {
    std::memcpy(Buf + O, P.first.data(), P.first.size());
    O += P.first.size();
    Buf[O++] = '\0';
    std::memcpy(Buf + O, P.second.data(), P.second.size());
    O += P.second.size();
    Buf[O++] = '\0';
  }
  *OutLen = Total;
  *OutPtrBuf = Buf;
}

// Inverse of GetRenameMap: same alternating null-terminated pair encoding.
API_EXPORT(void)
LLVMPY_NewOrcJIT_SetRenameMap(OrcEngine *Eng, uint64_t H, const char *Buf,
                              size_t Len) {
  RenameMap M;
  size_t i = 0;
  while (i < Len) {
    const char *Old = Buf + i;
    size_t OldLen = std::strlen(Old);
    i += OldLen + 1;
    if (i >= Len)
      break;
    const char *New = Buf + i;
    size_t NewLen = std::strlen(New);
    i += NewLen + 1;
    M[std::string(Old, OldLen)] = std::string(New, NewLen);
  }
  Eng->setRenameMap(H, std::move(M));
}

API_EXPORT(void)
LLVMPY_NewOrcJIT_SetObjectCache(OrcEngine *Eng, ObjCacheNotifyFn Notify) {
  if (!Notify) {
    Eng->setObjectCache(nullptr);
    return;
  }
  Eng->setObjectCache(std::make_unique<CallbackObjectCache>(Notify));
}

} // extern "C"
