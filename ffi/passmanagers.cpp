#include "core.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm-c/Transforms/IPO.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/IPO.h"

using namespace llvm;

extern "C" {

API_EXPORT(LLVMPassManagerRef)
LLVMPY_CreatePassManager()
{
    return LLVMCreatePassManager();
}

API_EXPORT(void)
LLVMPY_DisposePassManager(LLVMPassManagerRef PM)
{
    return LLVMDisposePassManager(PM);
}


API_EXPORT(LLVMPassManagerRef)
LLVMPY_CreateFunctionPassManager(LLVMModuleRef M)
{
    return LLVMCreateFunctionPassManagerForModule(M);
}

API_EXPORT(int)
LLVMPY_RunPassManager(LLVMPassManagerRef PM,
                      LLVMModuleRef M)
{
    return LLVMRunPassManager(PM, M);
}

API_EXPORT(int)
LLVMPY_RunFunctionPassManager(LLVMPassManagerRef PM,
                              LLVMValueRef F)
{
    return LLVMRunFunctionPassManager(PM, F);
}

API_EXPORT(int)
LLVMPY_InitializeFunctionPassManager(LLVMPassManagerRef FPM)
{
    return LLVMInitializeFunctionPassManager(FPM);
}

API_EXPORT(int)
LLVMPY_FinalizeFunctionPassManager(LLVMPassManagerRef FPM)
{
    return LLVMFinalizeFunctionPassManager(FPM);
}

API_EXPORT(void)
LLVMPY_AddConstantMergePass(LLVMPassManagerRef PM)
{
    LLVMAddConstantMergePass(PM);
}

API_EXPORT(void)
LLVMPY_AddDeadArgEliminationPass(LLVMPassManagerRef PM)
{
    LLVMAddDeadArgEliminationPass(PM);
}

API_EXPORT(void)
LLVMPY_AddFunctionAttrsPass(LLVMPassManagerRef PM)
{
    LLVMAddFunctionAttrsPass(PM);
}

API_EXPORT(void)
LLVMPY_AddFunctionInliningPass(LLVMPassManagerRef PM, int Threshold)
{
    unwrap(PM)->add(createFunctionInliningPass(Threshold));
}

API_EXPORT(void)
LLVMPY_AddGlobalOptimizerPass(LLVMPassManagerRef PM)
{
    LLVMAddGlobalOptimizerPass(PM);
}

API_EXPORT(void)
LLVMPY_AddGlobalDCEPass(LLVMPassManagerRef PM)
{
    LLVMAddGlobalDCEPass(PM);
}

API_EXPORT(void)
LLVMPY_AddIPSCCPPass(LLVMPassManagerRef PM)
{
    LLVMAddIPSCCPPass(PM);
}

API_EXPORT(void)
LLVMPY_AddDeadCodeEliminationPass(LLVMPassManagerRef PM)
{
    unwrap(PM)->add(createDeadCodeEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddCFGSimplificationPass(LLVMPassManagerRef PM)
{
    LLVMAddCFGSimplificationPass(PM);
}

API_EXPORT(void)
LLVMPY_AddGVNPass(LLVMPassManagerRef PM)
{
    LLVMAddGVNPass(PM);
}

API_EXPORT(void)
LLVMPY_AddInstructionCombiningPass(LLVMPassManagerRef PM)
{
    LLVMAddInstructionCombiningPass(PM);
}

API_EXPORT(void)
LLVMPY_AddLICMPass(LLVMPassManagerRef PM)
{
    LLVMAddLICMPass(PM);
}

API_EXPORT(void)
LLVMPY_AddSCCPPass(LLVMPassManagerRef PM)
{
    LLVMAddSCCPPass(PM);
}

API_EXPORT(void)
LLVMPY_AddSROAPass(LLVMPassManagerRef PM)
{
    unwrap(PM)->add(createSROAPass());
}

API_EXPORT(void)
LLVMPY_AddTypeBasedAliasAnalysisPass(LLVMPassManagerRef PM)
{
    LLVMAddTypeBasedAliasAnalysisPass(PM);
}

API_EXPORT(void)
LLVMPY_AddBasicAliasAnalysisPass(LLVMPassManagerRef PM)
{
    LLVMAddBasicAliasAnalysisPass(PM);
}

} // end extern "C"
