#include "core.h"

#include "llvm-c/ExecutionEngine.h"
#include "llvm-c/LLJIT.h"
#include "llvm-c/Object.h"
#include "llvm-c/Orc.h"
#include "llvm/ExecutionEngine/Orc/ExecutionUtils.h"
#include "llvm/ExecutionEngine/Orc/LLJIT.h"
#include "llvm/Object/ObjectFile.h"

using namespace llvm;
using namespace llvm::orc;

inline LLJIT *unwrap(LLVMOrcLLJITRef P) { return reinterpret_cast<LLJIT *>(P); }

inline TargetMachine *unwrap(LLVMTargetMachineRef TM) {
    return reinterpret_cast<TargetMachine *>(TM);
}

inline LLVMOrcJITTargetMachineBuilderRef wrap(JITTargetMachineBuilder *JTMB) {
    return reinterpret_cast<LLVMOrcJITTargetMachineBuilderRef>(JTMB);
}

// unwrap for LLVMObjectFileRef
// from Object/Object.cpp
namespace llvm {
namespace object {

inline OwningBinary<ObjectFile> *unwrap(LLVMObjectFileRef OF) {
    return reinterpret_cast<OwningBinary<ObjectFile> *>(OF);
}
} // namespace object
} // namespace llvm

extern "C" {

std::vector<ThreadSafeModule> GlobalTSMs;

API_EXPORT(LLVMOrcLLJITRef)
LLVMPY_CreateLLJITCompiler(LLVMTargetMachineRef tm, const char **OutError) {
    LLVMOrcLLJITRef jit;
    LLVMOrcLLJITBuilderRef builder = nullptr;

    if (tm) {
        // The following is based on
        // LLVMOrcJITTargetMachineBuilderCreateFromTargetMachine. However, we
        // can't use that directly because it destroys the target machine, but
        // we need to keep it alive because it is referenced by / shared with
        // other objects on the Python side.
        auto *template_tm = unwrap(tm);
        auto jtmb = new JITTargetMachineBuilder(template_tm->getTargetTriple());

        (*jtmb)
            .setCPU(template_tm->getTargetCPU().str())
            .setRelocationModel(template_tm->getRelocationModel())
            .setCodeModel(template_tm->getCodeModel())
            .setCodeGenOptLevel(template_tm->getOptLevel())
            .setFeatures(template_tm->getTargetFeatureString())
            .setOptions(template_tm->Options);

        builder = LLVMOrcCreateLLJITBuilder();
        LLVMOrcLLJITBuilderSetJITTargetMachineBuilder(builder, wrap(jtmb));
    }

    auto error = LLVMOrcCreateLLJIT(&jit, builder);

    unwrap(jit)->getIRCompileLayer().setNotifyCompiled(
        [](MaterializationResponsibility &R, ThreadSafeModule TSM) {
            // Move TSM to take ownership and preserve the module.
            GlobalTSMs.push_back(std::move(TSM));
        });

    if (error) {
        char *message = LLVMGetErrorMessage(error);
        *OutError = LLVMPY_CreateString(message);
        return nullptr;
    }

    return jit;
}

API_EXPORT(LLVMOrcResourceTrackerRef)
LLVMPY_AddIRModule(LLVMOrcLLJITRef JIT, LLVMModuleRef M) {
    auto llvm_ts_ctx = LLVMOrcCreateNewThreadSafeContext();
    auto tsm = LLVMOrcCreateNewThreadSafeModule(M, llvm_ts_ctx);

    LLVMOrcJITDylibRef JD = LLVMOrcLLJITGetMainJITDylib(JIT);
    LLVMOrcResourceTrackerRef RT = LLVMOrcJITDylibCreateResourceTracker(JD);
    LLVMErrorRef err = LLVMOrcLLJITAddLLVMIRModuleWithRT(JIT, RT, tsm);
    if (err)
        abort();

    LLVMOrcDisposeThreadSafeContext(llvm_ts_ctx);

    return RT;
}

API_EXPORT(void)
LLVMPY_RemoveIRModule(LLVMOrcResourceTrackerRef RT) {
    auto error = LLVMOrcResourceTrackerRemove(RT);

    if (error)
        abort();

    LLVMOrcReleaseResourceTracker(RT);
}

API_EXPORT(void)
LLVMPY_ReleaseResourceTracker(LLVMOrcResourceTrackerRef RT) {
    LLVMOrcReleaseResourceTracker(RT);
}

API_EXPORT(uint64_t)
LLVMPY_LLJITLookup(LLVMOrcLLJITRef JIT, const char *name,
                   const char **OutError) {
    // Based upon LLVMOrcLLJITLookup - however the use of that function results
    // in assertion errors when disposing of the LLJIT with the message:
    //
    //     llvm::orc::SymbolStringPool::~SymbolStringPool(): Assertion
    //     `Pool.empty() && "Dangling references at pool destruction time"'
    //     failed.
    //
    // if the lookup fails. Here we handle cleanup in the error case ourselves.

    auto sym = unwrap(JIT)->lookup(name);
    if (!sym) {
        char *message = LLVMGetErrorMessage(wrap(sym.takeError()));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);
        return 0;
    }

    return sym->getAddress();
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_LLJITGetDataLayout(LLVMOrcLLJITRef JIT) {
    return wrap(&unwrap(JIT)->getDataLayout());
}

API_EXPORT(void)
LLVMPY_LLJITDispose(LLVMOrcLLJITRef JIT) { LLVMOrcDisposeLLJIT(JIT); }

API_EXPORT(void)
LLVMPY_LLJITRunInitializers(LLVMOrcLLJITRef JIT) {
    auto lljit = unwrap(JIT);
    auto error = lljit->initialize(lljit->getMainJITDylib());

    if (error)
        abort();
}

API_EXPORT(void)
LLVMPY_LLJITRunDeinitializers(LLVMOrcLLJITRef JIT) {
    auto lljit = unwrap(JIT);
    auto error = lljit->deinitialize(lljit->getMainJITDylib());

    if (error)
        abort();
}

API_EXPORT(bool)
LLVMPY_LLJITDefineSymbol(LLVMOrcLLJITRef JIT, const char *name, void *addr,
                         const char **OutError) {
    auto lljit = unwrap(JIT);
    auto &JD = lljit->getMainJITDylib();
    SymbolStringPtr mangled = lljit->mangleAndIntern(name);
    JITEvaluatedSymbol symbol = JITEvaluatedSymbol::fromPointer(addr);
    auto error = JD.define(absoluteSymbols({{mangled, symbol}}));

    if (error) {
        char *message = LLVMGetErrorMessage(wrap(std::move(error)));
        *OutError = LLVMPY_CreateString(message);
        return true;
    }

    return false;
}

API_EXPORT(void)
LLVMPY_LLJITAddCurrentProcessSearch(LLVMOrcLLJITRef JIT) {
    auto lljit = unwrap(JIT);
    auto &JD = lljit->getMainJITDylib();
    auto prefix = lljit->getDataLayout().getGlobalPrefix();
    auto DLSGOrErr =
        DynamicLibrarySearchGenerator::GetForCurrentProcess(prefix);
    if (DLSGOrErr)
        JD.addGenerator(std::move(*DLSGOrErr));
    else
        abort();
}

API_EXPORT(bool)
LLVMPY_LLJITAddObjectFile(LLVMOrcLLJITRef JIT, LLVMObjectFileRef ObjF,
                          const char **OutError) {
    using namespace llvm::object;
    auto lljit = unwrap(JIT);
    auto object_file = unwrap(ObjF);
    auto binary_tuple = object_file->takeBinary();
    auto error = lljit->addObjectFile(std::move(binary_tuple.second));

    if (error) {
        char *message = LLVMGetErrorMessage(wrap(std::move(error)));
        *OutError = LLVMPY_CreateString(message);
        return true;
    }

    return false;
}

} // extern "C"
