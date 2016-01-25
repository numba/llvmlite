#include "core.h"
#include "llvm-c/Transforms/PassManagerBuilder.h"
#include "llvm-c/Target.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"


extern "C" {

namespace llvm {
    inline PassManagerBuilder *unwrap(LLVMPassManagerBuilderRef P) {
        return reinterpret_cast<PassManagerBuilder*>(P);
    }

    inline LLVMPassManagerBuilderRef wrap(PassManagerBuilder *P) {
        return reinterpret_cast<LLVMPassManagerBuilderRef>(P);
    }
}


API_EXPORT(LLVMPassManagerBuilderRef)
LLVMPY_PassManagerBuilderCreate()
{
    return LLVMPassManagerBuilderCreate();
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderDispose(LLVMPassManagerBuilderRef PMB)
{
    LLVMPassManagerBuilderDispose(PMB);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateModulePassManager(
                            LLVMPassManagerBuilderRef PMB,
                            LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateModulePassManager(PMB, PM);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetOptLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->OptLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    LLVMPassManagerBuilderSetOptLevel(PMB, OptLevel);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SizeLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    LLVMPassManagerBuilderSetSizeLevel(PMB, SizeLevel);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnitAtATime;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB,
                                            int Value)
{
    LLVMPassManagerBuilderSetDisableUnitAtATime(PMB, Value);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnrollLoops;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    LLVMPassManagerBuilderSetDisableUnrollLoops(PMB, Value);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(LLVMPassManagerBuilderRef PMB,
                                                 unsigned Threshold)
{
    LLVMPassManagerBuilderUseInlinerWithThreshold(PMB, Threshold);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                                        LLVMPassManagerBuilderRef PMB,
                                        LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateFunctionPassManager(PMB, PM);
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetLoopVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->LoopVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetLoopVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->LoopVectorize;
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSLPVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->SLPVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetSLPVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SLPVectorize;
}


} // end extern "C"
