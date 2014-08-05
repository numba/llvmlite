#include "core.h"
#include "llvm-c/ExecutionEngine.h"
#include <cstdio>

extern "C" {

void
LLVMPY_LinkInJIT() {
    LLVMLinkInJIT();
}

void
LLVMPY_LinkInMCJIT() {
    LLVMLinkInMCJIT();
}

void
LLVMPY_DisposeExecutionEngine(LLVMExecutionEngineRef EE)
{
    LLVMDisposeExecutionEngine(EE);
}

void
LLVMPY_AddModule(LLVMExecutionEngineRef EE,
              LLVMModuleRef M)
{
    LLVMAddModule(EE, M);
}

int
LLVMPY_RemoveModule(LLVMExecutionEngineRef EE,
                    LLVMModuleRef M,
                    char** OutError)
{
   return LLVMRemoveModule(EE, M, &M, OutError);
}

int
LLVMPY_CreateJITCompiler(LLVMExecutionEngineRef *OutEE,
                         LLVMModuleRef M,
                         unsigned OptLevel,
                         char **OutError)
{
    return LLVMCreateJITCompilerForModule(OutEE, M, OptLevel, OutError);
}

//int
//LLVMPY_CreateMCJITCompiler(LLVMExecutionEngineRef *OutEE,
//                           LLVMModuleRef M,
//                           unsigned OptLevel,
//                           char **OutError)
//{
//    return LLVMCreateMCJITCompilerForModule(OutEE, M, OptLevel, OutError);
//}

void*
LLVMPY_GetPointerToGlobal(LLVMExecutionEngineRef EE,
                          LLVMValueRef Global)
{
    return LLVMGetPointerToGlobal(EE, Global);
}

void
LLVMPY_AddGlobalMapping(LLVMExecutionEngineRef EE,
                        LLVMValueRef Global,
                        void *Addr)
{
    LLVMAddGlobalMapping(EE, Global, Addr);
}

} // end extern "C"
