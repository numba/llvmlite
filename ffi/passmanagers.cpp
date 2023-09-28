#include <sstream>

#include "core.h"

#include "llvm-c/Transforms/IPO.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm/ADT/STLExtras.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/ToolOutputFile.h"
#include "llvm/Support/YAMLTraits.h"
#include "llvm/Support/raw_ostream.h"

#include "llvm-c/Transforms/IPO.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm/IR/LLVMRemarkStreamer.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Remarks/RemarkStreamer.h"
#include "llvm/Transforms/IPO.h"
#include "llvm/Transforms/Scalar.h"

#include <llvm/IR/PassTimingInfo.h>

#include <llvm/Analysis/AliasAnalysisEvaluator.h>
#include <llvm/Analysis/BasicAliasAnalysis.h>
#include <llvm/Analysis/CFGPrinter.h>
#include <llvm/Analysis/CallPrinter.h>
#include <llvm/Analysis/DependenceAnalysis.h>
#include <llvm/Analysis/DomPrinter.h>
#include <llvm/Analysis/GlobalsModRef.h>
#include <llvm/Analysis/IVUsers.h>
#include <llvm/Analysis/Lint.h>
#include <llvm/Analysis/Passes.h>
#include <llvm/Analysis/ScalarEvolutionAliasAnalysis.h>
#include <llvm/CodeGen/Passes.h>
#include <llvm/Transforms/AggressiveInstCombine/AggressiveInstCombine.h>
#include <llvm/Transforms/IPO.h>
#include <llvm/Transforms/IPO/AlwaysInliner.h>
#include <llvm/Transforms/Utils.h>
#include <llvm/Transforms/Utils/UnifyFunctionExitNodes.h>
using namespace llvm;

/*
 * Exposed API
 */

extern "C" {

API_EXPORT(void)
LLVMPY_SetTimePasses(bool enable) { TimePassesIsEnabled = enable; }

API_EXPORT(void)
LLVMPY_ReportAndResetTimings(const char **outmsg) {
    std::string osbuf;
    raw_string_ostream os(osbuf);
    reportAndResetTimings(&os);
    os.flush();
    *outmsg = LLVMPY_CreateString(os.str().c_str());
}

API_EXPORT(LLVMPassManagerRef)
LLVMPY_CreatePassManager() { return LLVMCreatePassManager(); }

API_EXPORT(void)
LLVMPY_DisposePassManager(LLVMPassManagerRef PM) {
    return LLVMDisposePassManager(PM);
}

API_EXPORT(LLVMPassManagerRef)
LLVMPY_CreateFunctionPassManager(LLVMModuleRef M) {
    return LLVMCreateFunctionPassManagerForModule(M);
}

API_EXPORT(int)
LLVMPY_RunPassManagerWithRemarks(LLVMPassManagerRef PM, LLVMModuleRef M,
                                 const char *remarks_format,
                                 const char *remarks_filter,
                                 const char *record_filename) {
    auto setupResult = llvm::setupLLVMOptimizationRemarks(
        unwrap(M)->getContext(), record_filename, remarks_filter,
        remarks_format, true);
    if (!setupResult) {
        return -1;
    }
    auto optimisationFile = std::move(*setupResult);
    auto r = LLVMRunPassManager(PM, M);

    unwrap(M)->getContext().setMainRemarkStreamer(nullptr);
    unwrap(M)->getContext().setLLVMRemarkStreamer(nullptr);

    optimisationFile->keep();
    optimisationFile->os().flush();
    return r;
}

API_EXPORT(int)
LLVMPY_RunPassManager(LLVMPassManagerRef PM, LLVMModuleRef M) {
    return LLVMRunPassManager(PM, M);
}

API_EXPORT(int)
LLVMPY_RunFunctionPassManagerWithRemarks(LLVMPassManagerRef PM, LLVMValueRef F,
                                         const char *remarks_format,
                                         const char *remarks_filter,
                                         const char *record_filename) {
    auto setupResult = llvm::setupLLVMOptimizationRemarks(
        unwrap(F)->getContext(), record_filename, remarks_filter,
        remarks_format, true);
    if (!setupResult) {
        return -1;
    }
    auto optimisationFile = std::move(*setupResult);

    auto r = LLVMRunFunctionPassManager(PM, F);

    unwrap(F)->getContext().setMainRemarkStreamer(nullptr);
    unwrap(F)->getContext().setLLVMRemarkStreamer(nullptr);

    optimisationFile->keep();
    optimisationFile->os().flush();
    return r;
}

API_EXPORT(int)
LLVMPY_RunFunctionPassManager(LLVMPassManagerRef PM, LLVMValueRef F) {
    return LLVMRunFunctionPassManager(PM, F);
}

API_EXPORT(int)
LLVMPY_InitializeFunctionPassManager(LLVMPassManagerRef FPM) {
    return LLVMInitializeFunctionPassManager(FPM);
}

API_EXPORT(int)
LLVMPY_FinalizeFunctionPassManager(LLVMPassManagerRef FPM) {
    return LLVMFinalizeFunctionPassManager(FPM);
}

API_EXPORT(void)
LLVMPY_AddAAEvalPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createAAEvalPass());
}

API_EXPORT(void)
LLVMPY_AddBasicAAWrapperPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createBasicAAWrapperPass());
}

API_EXPORT(void)
LLVMPY_AddDependenceAnalysisPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createDependenceAnalysisWrapperPass());
}

API_EXPORT(void)
LLVMPY_AddCallGraphDOTPrinterPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createCallGraphDOTPrinterPass());
}

API_EXPORT(void)
LLVMPY_AddDotDomPrinterPass(LLVMPassManagerRef PM, bool showBody) {
    unwrap(PM)->add(showBody ? llvm::createDomPrinterPass()
                             : llvm::createDomOnlyPrinterPass());
}

API_EXPORT(void)
LLVMPY_AddGlobalsModRefAAPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createGlobalsAAWrapperPass());
}

API_EXPORT(void)
LLVMPY_AddDotPostDomPrinterPass(LLVMPassManagerRef PM, bool showBody) {
    unwrap(PM)->add(showBody ? llvm::createPostDomPrinterPass()
                             : llvm::createPostDomOnlyPrinterPass());
}

API_EXPORT(void)
LLVMPY_AddCFGPrinterPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createCFGPrinterLegacyPassPass());
}

API_EXPORT(void)
LLVMPY_AddConstantMergePass(LLVMPassManagerRef PM) {
    LLVMAddConstantMergePass(PM);
}

API_EXPORT(void)
LLVMPY_AddDeadStoreEliminationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createDeadStoreEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddReversePostOrderFunctionAttrsPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createReversePostOrderFunctionAttrsPass());
}

API_EXPORT(void)
LLVMPY_AddDeadArgEliminationPass(LLVMPassManagerRef PM) {
    LLVMAddDeadArgEliminationPass(PM);
}

API_EXPORT(void)
LLVMPY_AddInstructionCountPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createInstCountPass());
}

API_EXPORT(void)
LLVMPY_AddIVUsersPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createIVUsersPass());
}

API_EXPORT(void)
LLVMPY_AddLazyValueInfoPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createLazyValueInfoPass());
}
API_EXPORT(void)
LLVMPY_AddLintPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createLintLegacyPassPass());
}
API_EXPORT(void)
LLVMPY_AddModuleDebugInfoPrinterPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createModuleDebugInfoPrinterPass());
}

API_EXPORT(void)
LLVMPY_AddRegionInfoPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createRegionInfoPass());
}

API_EXPORT(void)
LLVMPY_AddScalarEvolutionAAPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createSCEVAAWrapperPass());
}

API_EXPORT(void)
LLVMPY_AddAggressiveDCEPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createAggressiveDCEPass());
}

API_EXPORT(void)
LLVMPY_AddAlwaysInlinerPass(LLVMPassManagerRef PM, bool insertLifetime) {
    unwrap(PM)->add(llvm::createAlwaysInlinerLegacyPass(insertLifetime));
}

API_EXPORT(void)
LLVMPY_AddArgPromotionPass(LLVMPassManagerRef PM, unsigned int maxElements) {
    unwrap(PM)->add(llvm::createArgumentPromotionPass(maxElements));
}

API_EXPORT(void)
LLVMPY_AddBreakCriticalEdgesPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(llvm::createBreakCriticalEdgesPass());
}

API_EXPORT(void)
LLVMPY_AddFunctionAttrsPass(LLVMPassManagerRef PM) {
    LLVMAddFunctionAttrsPass(PM);
}

API_EXPORT(void)
LLVMPY_AddFunctionInliningPass(LLVMPassManagerRef PM, int Threshold) {
    unwrap(PM)->add(createFunctionInliningPass(Threshold));
}

API_EXPORT(void)
LLVMPY_AddGlobalOptimizerPass(LLVMPassManagerRef PM) {
    LLVMAddGlobalOptimizerPass(PM);
}

API_EXPORT(void)
LLVMPY_AddGlobalDCEPass(LLVMPassManagerRef PM) { LLVMAddGlobalDCEPass(PM); }

API_EXPORT(void)
LLVMPY_AddIPSCCPPass(LLVMPassManagerRef PM) { LLVMAddIPSCCPPass(PM); }

API_EXPORT(void)
LLVMPY_AddDeadCodeEliminationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createDeadCodeEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddAggressiveInstructionCombiningPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createAggressiveInstCombinerPass());
}

API_EXPORT(void)
LLVMPY_AddInternalizePass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createInternalizePass());
}

API_EXPORT(void)
LLVMPY_AddJumpThreadingPass(LLVMPassManagerRef PM, int threshold) {
    unwrap(PM)->add(createJumpThreadingPass(threshold));
}

API_EXPORT(void)
LLVMPY_AddLCSSAPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLCSSAPass());
}

API_EXPORT(void)
LLVMPY_AddLoopDeletionPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLoopDeletionPass());
}

API_EXPORT(void)
LLVMPY_AddLoopExtractorPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLoopExtractorPass());
}

API_EXPORT(void)
LLVMPY_AddSingleLoopExtractorPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createSingleLoopExtractorPass());
}

API_EXPORT(void)
LLVMPY_AddLoopStrengthReducePass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLoopStrengthReducePass());
}

API_EXPORT(void)
LLVMPY_AddLoopSimplificationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLoopSimplifyPass());
}

API_EXPORT(void)
LLVMPY_AddLoopUnrollPass(LLVMPassManagerRef PM) { LLVMAddLoopUnrollPass(PM); }

API_EXPORT(void)
LLVMPY_AddLoopUnrollAndJamPass(LLVMPassManagerRef PM) {
    LLVMAddLoopUnrollAndJamPass(PM);
}

API_EXPORT(void)
LLVMPY_AddLoopUnswitchPass(LLVMPassManagerRef PM, bool optimizeForSize,
                           bool hasBranchDivergence) {
    unwrap(PM)->add(
        createLoopUnswitchPass(optimizeForSize, hasBranchDivergence));
}

API_EXPORT(void)
LLVMPY_AddLowerAtomicPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLowerAtomicPass());
}

API_EXPORT(void)
LLVMPY_AddLowerInvokePass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLowerInvokePass());
}

API_EXPORT(void)
LLVMPY_AddLowerSwitchPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLowerSwitchPass());
}

API_EXPORT(void)
LLVMPY_AddMemCpyOptimizationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createMemCpyOptPass());
}

API_EXPORT(void)
LLVMPY_AddMergeFunctionsPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createMergeFunctionsPass());
}

API_EXPORT(void)
LLVMPY_AddMergeReturnsPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createUnifyFunctionExitNodesPass());
}

API_EXPORT(void)
LLVMPY_AddPartialInliningPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createPartialInliningPass());
}

API_EXPORT(void)
LLVMPY_AddPruneExceptionHandlingPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createPruneEHPass());
}

API_EXPORT(void)
LLVMPY_AddReassociatePass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createReassociatePass());
}

API_EXPORT(void)
LLVMPY_AddDemoteRegisterToMemoryPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createDemoteRegisterToMemoryPass());
}

API_EXPORT(void)
LLVMPY_AddSinkPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createSinkingPass());
}

API_EXPORT(void)
LLVMPY_AddStripSymbolsPass(LLVMPassManagerRef PM, bool onlyDebugInfo) {
    unwrap(PM)->add(createStripSymbolsPass(onlyDebugInfo));
}

API_EXPORT(void)
LLVMPY_AddStripDeadDebugInfoPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createStripDeadDebugInfoPass());
}

API_EXPORT(void)
LLVMPY_AddStripDeadPrototypesPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createStripDeadPrototypesPass());
}

API_EXPORT(void)
LLVMPY_AddStripDebugDeclarePrototypesPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createStripDebugDeclarePass());
}

API_EXPORT(void)
LLVMPY_AddStripNondebugSymbolsPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createStripNonDebugSymbolsPass());
}

API_EXPORT(void)
LLVMPY_AddTailCallEliminationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createTailCallEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddCFGSimplificationPass(LLVMPassManagerRef PM) {
    LLVMAddCFGSimplificationPass(PM);
}

API_EXPORT(void)
LLVMPY_AddGVNPass(LLVMPassManagerRef PM) { LLVMAddGVNPass(PM); }

API_EXPORT(void)
LLVMPY_AddInstructionCombiningPass(LLVMPassManagerRef PM) {
    LLVMAddInstructionCombiningPass(PM);
}

API_EXPORT(void)
LLVMPY_AddLICMPass(LLVMPassManagerRef PM) { LLVMAddLICMPass(PM); }

API_EXPORT(void)
LLVMPY_AddSCCPPass(LLVMPassManagerRef PM) { LLVMAddSCCPPass(PM); }

API_EXPORT(void)
LLVMPY_AddSROAPass(LLVMPassManagerRef PM) { unwrap(PM)->add(createSROAPass()); }

API_EXPORT(void)
LLVMPY_AddTypeBasedAliasAnalysisPass(LLVMPassManagerRef PM) {
    LLVMAddTypeBasedAliasAnalysisPass(PM);
}

API_EXPORT(void)
LLVMPY_AddBasicAliasAnalysisPass(LLVMPassManagerRef PM) {
    LLVMAddBasicAliasAnalysisPass(PM);
}

API_EXPORT(void)
LLVMPY_LLVMAddLoopRotatePass(LLVMPassManagerRef PM) {
    LLVMAddLoopRotatePass(PM);
}

API_EXPORT(void)
LLVMPY_AddInstructionNamerPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createInstructionNamerPass());
}

} // end extern "C"
