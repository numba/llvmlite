#include "core.h"
#include "llvm-c/Target.h"
#include "llvm-c/TargetMachine.h"
#include "llvm/ADT/Triple.h"
#include "llvm/Analysis/TargetLibraryInfo.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Type.h"
#include "llvm/MC/TargetRegistry.h"
#include "llvm/Support/Host.h"
#include "llvm/Target/TargetMachine.h"

#include <cstdio>
#include <cstring>
#include <sstream>

namespace llvm {

inline Target *unwrap(LLVMTargetRef T) { return reinterpret_cast<Target *>(T); }

inline TargetMachine *unwrap(LLVMTargetMachineRef TM) {
    return reinterpret_cast<TargetMachine *>(TM);
}

inline LLVMTargetMachineRef wrap(TargetMachine *TM) {
    return reinterpret_cast<LLVMTargetMachineRef>(TM);
}

} // namespace llvm

extern "C" {

API_EXPORT(void)
LLVMPY_GetProcessTriple(const char **Out) {
    *Out = LLVMPY_CreateString(llvm::sys::getProcessTriple().c_str());
}

/**
 * Output the feature string to the output argument.
 * Features are prefixed with '+' or '-' for enabled or disabled, respectively.
 * Features are separated by ','.
 */
API_EXPORT(int)
LLVMPY_GetHostCPUFeatures(const char **Out) {
    llvm::StringMap<bool> features;
    std::ostringstream buf;
    if (llvm::sys::getHostCPUFeatures(features)) {
        for (auto &F : features) {
            if (buf.tellp()) {
                buf << ',';
            }
            buf << ((F.second ? "+" : "-") + F.first()).str();
        }
        *Out = LLVMPY_CreateString(buf.str().c_str());
        return 1;
    }
    return 0;
}

API_EXPORT(void)
LLVMPY_GetDefaultTargetTriple(const char **Out) {
    *Out = LLVMPY_CreateString(llvm::sys::getDefaultTargetTriple().c_str());
}

API_EXPORT(void)
LLVMPY_GetHostCPUName(const char **Out) {
    *Out = LLVMPY_CreateString(llvm::sys::getHostCPUName().data());
}

API_EXPORT(int)
LLVMPY_GetTripleObjectFormat(const char *tripleStr) {
    return llvm::Triple(tripleStr).getObjectFormat();
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_CreateTargetData(const char *StringRep) {
    return LLVMCreateTargetData(StringRep);
}

API_EXPORT(void)
LLVMPY_CopyStringRepOfTargetData(LLVMTargetDataRef TD, char **Out) {
    *Out = LLVMCopyStringRepOfTargetData(TD);
}

API_EXPORT(void)
LLVMPY_DisposeTargetData(LLVMTargetDataRef TD) { LLVMDisposeTargetData(TD); }

API_EXPORT(long long)
LLVMPY_ABISizeOfType(LLVMTargetDataRef TD, LLVMTypeRef Ty) {
    return (long long)LLVMABISizeOfType(TD, Ty);
}

API_EXPORT(long long)
LLVMPY_OffsetOfElement(LLVMTargetDataRef TD, LLVMTypeRef Ty, int Element) {
    llvm::Type *tp = llvm::unwrap(Ty);
    if (!tp->isStructTy())
        return -1;
    return (long long)LLVMOffsetOfElement(TD, Ty, Element);
}

API_EXPORT(long long)
LLVMPY_ABISizeOfElementType(LLVMTargetDataRef TD, LLVMTypeRef Ty) {
    llvm::Type *tp = llvm::unwrap(Ty);
    if (!tp->isPointerTy())
        return -1;
    tp = tp->getPointerElementType();
    return (long long)LLVMABISizeOfType(TD, llvm::wrap(tp));
}

API_EXPORT(long long)
LLVMPY_ABIAlignmentOfElementType(LLVMTargetDataRef TD, LLVMTypeRef Ty) {
    llvm::Type *tp = llvm::unwrap(Ty);
    if (!tp->isPointerTy())
        return -1;
    tp = tp->getPointerElementType();
    return (long long)LLVMABIAlignmentOfType(TD, llvm::wrap(tp));
}

API_EXPORT(LLVMTargetRef)
LLVMPY_GetTargetFromTriple(const char *Triple, const char **ErrOut) {
    char *ErrorMessage;
    LLVMTargetRef T;
    if (LLVMGetTargetFromTriple(Triple, &T, &ErrorMessage)) {
        *ErrOut = LLVMPY_CreateString(ErrorMessage);
        LLVMDisposeMessage(ErrorMessage);
        return NULL;
    }
    return T;
}

API_EXPORT(const char *)
LLVMPY_GetTargetName(LLVMTargetRef T) { return LLVMGetTargetName(T); }

API_EXPORT(const char *)
LLVMPY_GetTargetDescription(LLVMTargetRef T) {
    return LLVMGetTargetDescription(T);
}

API_EXPORT(LLVMTargetMachineRef)
LLVMPY_CreateTargetMachine(LLVMTargetRef T, const char *Triple, const char *CPU,
                           const char *Features, int OptLevel,
                           const char *RelocModel, const char *CodeModel,
                           int PrintMC, int JIT, const char *ABIName) {
    using namespace llvm;
    CodeGenOpt::Level cgol;
    switch (OptLevel) {
    case 0:
        cgol = CodeGenOpt::None;
        break;
    case 1:
        cgol = CodeGenOpt::Less;
        break;
    case 3:
        cgol = CodeGenOpt::Aggressive;
        break;
    case 2:
    default:
        cgol = CodeGenOpt::Default;
    }

    CodeModel::Model cm;
    std::string cms(CodeModel);
    if (cms == "small")
        cm = CodeModel::Small;
    else if (cms == "kernel")
        cm = CodeModel::Kernel;
    else if (cms == "medium")
        cm = CodeModel::Medium;
    else if (cms == "large")
        cm = CodeModel::Large;
    else if (cms == "default") // As per LLVM 5, needed for AOT
        cm = CodeModel::Small;
    else { // catches "jitdefault" and not set, as per LLVM 5, needed for MCJIT
        // fall through, use model based on bitness
        int bits = sizeof(void *);
        if (bits == 4)
            cm = CodeModel::Small;
        else
            cm = CodeModel::Large;
    }

    Optional<Reloc::Model> rm;
    std::string rms(RelocModel);
    if (rms == "static")
        rm = Reloc::Static;
    else if (rms == "pic")
        rm = Reloc::PIC_;
    else if (rms == "dynamicnopic")
        rm = Reloc::DynamicNoPIC;

    TargetOptions opt;
    opt.MCOptions.ShowMCInst = PrintMC;
    opt.MCOptions.ABIName = ABIName;

    bool jit = JIT;

    return wrap(unwrap(T)->createTargetMachine(Triple, CPU, Features, opt, rm,
                                               cm, cgol, jit));
}

API_EXPORT(void)
LLVMPY_DisposeTargetMachine(LLVMTargetMachineRef TM) {
    return LLVMDisposeTargetMachine(TM);
}

API_EXPORT(void)
LLVMPY_GetTargetMachineTriple(LLVMTargetMachineRef TM, const char **Out) {
    // result is already strdup()ed by LLVMGetTargetMachineTriple
    *Out = LLVMGetTargetMachineTriple(TM);
}

API_EXPORT(void)
LLVMPY_SetTargetMachineAsmVerbosity(LLVMTargetMachineRef TM, int verbose) {
    LLVMSetTargetMachineAsmVerbosity(TM, verbose);
}

API_EXPORT(LLVMMemoryBufferRef)
LLVMPY_TargetMachineEmitToMemory(LLVMTargetMachineRef TM, LLVMModuleRef M,
                                 int use_object, const char **ErrOut) {
    LLVMCodeGenFileType filetype = LLVMAssemblyFile;
    if (use_object)
        filetype = LLVMObjectFile;

    char *ErrorMessage;
    LLVMMemoryBufferRef BufOut;
    int err = LLVMTargetMachineEmitToMemoryBuffer(TM, M, filetype,
                                                  &ErrorMessage, &BufOut);
    if (err) {
        *ErrOut = LLVMPY_CreateString(ErrorMessage);
        LLVMDisposeMessage(ErrorMessage);
        return NULL;
    }

    return BufOut;
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_CreateTargetMachineData(LLVMTargetMachineRef TM) {
    return llvm::wrap(
        new llvm::DataLayout(llvm::unwrap(TM)->createDataLayout()));
}

API_EXPORT(void)
LLVMPY_AddAnalysisPasses(LLVMTargetMachineRef TM, LLVMPassManagerRef PM) {
    LLVMAddAnalysisPasses(TM, PM);
}

API_EXPORT(const void *)
LLVMPY_GetBufferStart(LLVMMemoryBufferRef MB) { return LLVMGetBufferStart(MB); }

API_EXPORT(size_t)
LLVMPY_GetBufferSize(LLVMMemoryBufferRef MB) { return LLVMGetBufferSize(MB); }

API_EXPORT(void)
LLVMPY_DisposeMemoryBuffer(LLVMMemoryBufferRef MB) {
    return LLVMDisposeMemoryBuffer(MB);
}

API_EXPORT(int)
LLVMPY_HasSVMLSupport(void) {
#ifdef HAVE_SVML
    return 1;
#else
    return 0;
#endif
}

API_EXPORT(void)
LLVMPY_AddTargetLibraryInfoPass(LLVMPassManagerRef PM, const char *TripleStr) {
    using namespace llvm;
    unwrap(PM)->add(new TargetLibraryInfoWrapperPass(Triple(TripleStr)));
}

} // end extern "C"
