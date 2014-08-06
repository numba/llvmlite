#include "core.h"


extern "C" {

LLVMPassManagerRef
LLVMPY_CreatePassManager()
{
    return LLVMCreatePassManager();
}

void
LLVMPY_DisposePassManager(LLVMPassManagerRef PM)
{
    return LLVMDisposePassManager(PM);
}


LLVMPassManagerRef
LLVMPY_CreateFunctionPassManager(LLVMModuleRef M)
{
    return LLVMCreateFunctionPassManagerForModule(M);
}

int
LLVMPY_RunPassManager(LLVMPassManagerRef PM,
                      LLVMModuleRef M)
{
    return LLVMRunPassManager(PM, M);
}

int
LLVMPY_RunFunctionPassManager(LLVMPassManagerRef PM,
                              LLVMValueRef F)
{
    return LLVMRunFunctionPassManager(PM, F);
}

int
LLVMPY_InitializeFunctionPassManager(LLVMPassManagerRef FPM)
{
    return LLVMInitializeFunctionPassManager(FPM);
}

int
LLVMPY_FinalizeFunctionPassManager(LLVMPassManagerRef FPM)
{
    return LLVMFinalizeFunctionPassManager(FPM);
}

} // end extern "C"
