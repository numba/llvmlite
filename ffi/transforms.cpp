#include "core.h"
#include "llvm-c/Transforms/PassManagerBuilder.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

extern "C" {

namespace llvm {
    inline PassManagerBuilder *unwrap(LLVMPassManagerBuilderRef P) {
        return reinterpret_cast<PassManagerBuilder*>(P);
    }

    inline LLVMPassManagerBuilderRef wrap(PassManagerBuilder *P) {
      return reinterpret_cast<LLVMPassManagerBuilderRef>(P);
    }
};

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

unsigned
LLVMPY_PassManagerBuilderGetOptLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->OptLevel;
}

void
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    LLVMPassManagerBuilderSetOptLevel(PMB, OptLevel);
}

unsigned
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SizeLevel;
}

void
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    LLVMPassManagerBuilderSetSizeLevel(PMB, SizeLevel);
}

int
LLVMPY_PassManagerBuilderGetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnitAtATime;
}

void
LLVMPY_PassManagerBuilderSetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB,
                                            int Value)
{
    LLVMPassManagerBuilderSetDisableUnitAtATime(PMB, Value);
}

int
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnrollLoops;
}

void
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    LLVMPassManagerBuilderSetDisableUnrollLoops(PMB, Value);
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


