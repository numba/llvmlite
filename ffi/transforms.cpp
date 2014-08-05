//    LLVMPassManagerBuilderRef 	LLVMPassManagerBuilderCreate (void)
//    void 	LLVMPassManagerBuilderDispose (LLVMPassManagerBuilderRef PMB)
//    void 	LLVMPassManagerBuilderSetOptLevel (LLVMPassManagerBuilderRef PMB, unsigned OptLevel)
//    void 	LLVMPassManagerBuilderSetSizeLevel (LLVMPassManagerBuilderRef PMB, unsigned SizeLevel)
//    void 	LLVMPassManagerBuilderSetDisableUnitAtATime (LLVMPassManagerBuilderRef PMB, LLVMBool Value)
//    void 	LLVMPassManagerBuilderSetDisableUnrollLoops (LLVMPassManagerBuilderRef PMB, LLVMBool Value)
//    void 	LLVMPassManagerBuilderSetDisableSimplifyLibCalls (LLVMPassManagerBuilderRef PMB, LLVMBool Value)
//    void 	LLVMPassManagerBuilderUseInlinerWithThreshold (LLVMPassManagerBuilderRef PMB, unsigned Threshold)
//    void 	LLVMPassManagerBuilderPopulateFunctionPassManager (LLVMPassManagerBuilderRef PMB, LLVMPassManagerRef PM)
//    void 	LLVMPassManagerBuilderPopulateModulePassManager (LLVMPassManagerBuilderRef PMB, LLVMPassManagerRef PM)
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


} // end extern "C"


