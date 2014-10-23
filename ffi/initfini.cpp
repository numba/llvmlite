#include "llvm-c/Core.h"
#include "llvm-c/Initialization.h"
#include "llvm-c/Target.h"

#include "core.h"

extern "C" {


#define INIT(F) \
    API_EXPORT(void) LLVMPY_Initialize ## F() { \
            LLVMInitialize ## F (LLVMGetGlobalPassRegistry()); }

INIT(Core)
INIT(TransformUtils)
INIT(ScalarOpts)
INIT(ObjCARCOpts)
INIT(Vectorization)
INIT(InstCombine)
INIT(IPO)
// INIT(Instrumentation)
INIT(Analysis)
INIT(IPA)
INIT(CodeGen)
INIT(Target)

#undef INIT

API_EXPORT(void)
LLVMPY_Shutdown(){
    LLVMShutdown();
}

// Target Initialization
#define INIT(F) API_EXPORT(void) LLVMPY_Initialize ## F() { LLVMInitialize ## F (); }

// NOTE: it is important that we don't export functions which we don't use,
// especially those which may pull in large amounts of additional code or data.

// INIT(AllTargetInfos)
// INIT(AllTargets)
// INIT(AllTargetMCs)
INIT(NativeTarget)
INIT(NativeAsmParser)
INIT(NativeAsmPrinter)
// INIT(NativeDisassembler)

#undef INIT


} // end extern "C"


