#include "llvm-c/Core.h"
#include "llvm-c/Target.h"

#include "core.h"
#include "llvm/Config/llvm-config.h"
#include "llvm/InitializePasses.h"
#include "llvm/PassRegistry.h"

extern "C" {

#define INIT(F)                                                                \
    API_EXPORT(void) LLVMPY_Initialize##F() {                                  \
        llvm::initialize##F(*llvm::PassRegistry::getPassRegistry());           \
    }

INIT(Core)
INIT(TransformUtils)
INIT(ScalarOpts)
// https://github.com/llvm/llvm-project/commit/4153f989bab0f2f300fa8d3001ebeef7b6d9672c
// INIT(ObjCARCOpts)
INIT(Vectorization)
INIT(InstCombine)
INIT(IPO)
// INIT(Instrumentation)
INIT(Analysis)
// https://reviews.llvm.org/D145043, done in Analysis
// INIT(IPA)
INIT(CodeGen)
INIT(Target)

#undef INIT

API_EXPORT(void)
LLVMPY_Shutdown() { LLVMShutdown(); }

// Target Initialization
#define INIT(F)                                                                \
    API_EXPORT(void) LLVMPY_Initialize##F() { LLVMInitialize##F(); }

// NOTE: it is important that we don't export functions which we don't use,
// especially those which may pull in large amounts of additional code or data.

INIT(AllTargetInfos)
INIT(AllTargets)
INIT(AllTargetMCs)
INIT(AllAsmPrinters)
INIT(NativeTarget)
INIT(NativeAsmParser)
INIT(NativeAsmPrinter)
// INIT(NativeDisassembler)

#undef INIT

API_EXPORT(unsigned int)
LLVMPY_GetVersionInfo() {
    unsigned int verinfo = 0;
    verinfo += LLVM_VERSION_MAJOR << 16;
    verinfo += LLVM_VERSION_MINOR << 8;
#ifdef LLVM_VERSION_PATCH
    /* Not available under Windows... */
    verinfo += LLVM_VERSION_PATCH << 0;
#endif
    return verinfo;
}

} // end extern "C"
