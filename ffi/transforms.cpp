//    void 	LLVMPassManagerBuilderPopulateLTOPassManager (LLVMPassManagerBuilderRef PMB, LLVMPassManagerRef PM, LLVMBool Internalize, LLVMBool RunInliner)


#include "core.h"
#include "llvm-c/Transforms/PassManagerBuilder.h"

extern "C" {

LLVMPassManagerBuilderRef
LLVMPY_PassManagerBuilderCreate()
{
    return LLVMPassManagerBuilderCreate();
}

void
LLVMPY_PassManagerBuilderDispose(LLVMPassManagerBuilderRef PMB)
{
    LLVMPassManagerBuilderDispose(PMB);
}

void
LLVMPY_PassManagerBuilderPopulateModulePassManager(
                            LLVMPassManagerBuilderRef PMB,
                            LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateModulePassManager(PMB, PM);
}

void
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    LLVMPassManagerBuilderSetOptLevel(PMB, OptLevel);
}

void
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    LLVMPassManagerBuilderSetSizeLevel(PMB, SizeLevel);
}

void
LLVMPY_PassManagerBuilderSetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB,
                                            int Value)
{
    LLVMPassManagerBuilderSetDisableUnitAtATime(PMB, Value);
}

void
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    LLVMPassManagerBuilderSetDisableUnrollLoops(PMB, Value);
}


void
LLVMPY_PassManagerBuilderSetDisableSimplifyLibCalls(
                                    LLVMPassManagerBuilderRef PMB,
                                    int Value)
{
    LLVMPassManagerBuilderSetDisableSimplifyLibCalls(PMB, Value);
}

void
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(LLVMPassManagerBuilderRef PMB,
                                                 unsigned Threshold)
{
    LLVMPassManagerBuilderUseInlinerWithThreshold(PMB, Threshold);
}

void
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                                        LLVMPassManagerBuilderRef PMB,
                                        LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateFunctionPassManager(PMB, PM);
}



} // end extern "C"


