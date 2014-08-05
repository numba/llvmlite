#include "llvm-c/Core.h"
#include "llvm-c/Initialization.h"
#include "llvm-c/Target.h"
#include "llvm/Support/Host.h"

#include "core.h"

extern "C" {


#define INIT(F) \
    void LLVMPY_Initialize ## F() { \
            LLVMInitialize ## F (LLVMGetGlobalPassRegistry()); }

INIT(Core)
INIT(TransformUtils)
INIT(ScalarOpts)
INIT(ObjCARCOpts)
INIT(Vectorization)
INIT(InstCombine)
INIT(IPO)
INIT(Instrumentation)
INIT(Analysis)
INIT(IPA)
INIT(CodeGen)
INIT(Target)

#undef INIT

void
LLVMPY_Shutdown(){
    LLVMShutdown();
}


// Target Initialization
#define INIT(F) void LLVMPY_Initialize ## F() { LLVMInitialize ## F (); }

INIT(AllTargetInfos)
INIT(AllTargets)
INIT(AllTargetMCs)
INIT(NativeTarget)
//INIT(NativeAsmParser)
//INIT(NativeAsmPrinter)
//INIT(NativeDisassembler)

#undef INIT


void
LLVMPY_GetDefaultTargetTriple(const char **Out){
    using namespace llvm;
    *Out = LLVMPY_CreateString(sys::getDefaultTargetTriple().c_str());
}



} // end extern "C"


