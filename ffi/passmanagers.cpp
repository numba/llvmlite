#include <sstream>

#include "core.h"

#include "llvm/ADT/STLExtras.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/ToolOutputFile.h"
#include "llvm/Support/YAMLTraits.h"
#include "llvm/Support/raw_ostream.h"

// From PassBuilder.cpp
#include "llvm/Analysis/AliasAnalysisEvaluator.h"
#include "llvm/Analysis/AliasSetTracker.h"
#include "llvm/Analysis/AssumptionCache.h"
#include "llvm/Analysis/BasicAliasAnalysis.h"
#include "llvm/Analysis/BlockFrequencyInfo.h"
#include "llvm/Analysis/BranchProbabilityInfo.h"
#include "llvm/Analysis/CFGPrinter.h"
#include "llvm/Analysis/CFGSCCPrinter.h"
#include "llvm/Analysis/CGSCCPassManager.h"
#include "llvm/Analysis/CallGraph.h"
#include "llvm/Analysis/CallPrinter.h"
#include "llvm/Analysis/CostModel.h"
#include "llvm/Analysis/CycleAnalysis.h"
#include "llvm/Analysis/DDG.h"
#include "llvm/Analysis/DDGPrinter.h"
#include "llvm/Analysis/Delinearization.h"
#include "llvm/Analysis/DemandedBits.h"
#include "llvm/Analysis/DependenceAnalysis.h"
#include "llvm/Analysis/DomPrinter.h"
#include "llvm/Analysis/DominanceFrontier.h"
#include "llvm/Analysis/FunctionPropertiesAnalysis.h"
#include "llvm/Analysis/GlobalsModRef.h"
#include "llvm/Analysis/IRSimilarityIdentifier.h"
#include "llvm/Analysis/IVUsers.h"
#include "llvm/Analysis/InlineAdvisor.h"
#include "llvm/Analysis/InlineSizeEstimatorAnalysis.h"
#include "llvm/Analysis/InstCount.h"
#include "llvm/Analysis/LazyCallGraph.h"
#include "llvm/Analysis/LazyValueInfo.h"
#include "llvm/Analysis/Lint.h"
#include "llvm/Analysis/LoopAccessAnalysis.h"
#include "llvm/Analysis/LoopCacheAnalysis.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/LoopNestAnalysis.h"
#include "llvm/Analysis/MemDerefPrinter.h"
#include "llvm/Analysis/MemoryDependenceAnalysis.h"
#include "llvm/Analysis/MemorySSA.h"
#include "llvm/Analysis/ModuleDebugInfoPrinter.h"
#include "llvm/Analysis/ModuleSummaryAnalysis.h"
#include "llvm/Analysis/MustExecute.h"
#include "llvm/Analysis/ObjCARCAliasAnalysis.h"
#include "llvm/Analysis/OptimizationRemarkEmitter.h"
#include "llvm/Analysis/PhiValues.h"
#include "llvm/Analysis/PostDominators.h"
#include "llvm/Analysis/ProfileSummaryInfo.h"
#include "llvm/Analysis/RegionInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionAliasAnalysis.h"
#include "llvm/Analysis/ScopedNoAliasAA.h"
#include "llvm/Analysis/StackLifetime.h"
#include "llvm/Analysis/StackSafetyAnalysis.h"
#include "llvm/Analysis/TargetLibraryInfo.h"
#include "llvm/Analysis/TargetTransformInfo.h"
#include "llvm/Analysis/TypeBasedAliasAnalysis.h"
#include "llvm/Analysis/UniformityAnalysis.h"
#include "llvm/CodeGen/HardwareLoops.h"
#include "llvm/CodeGen/TypePromotion.h"
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/PrintPasses.h"
#include "llvm/IR/SafepointIRVerifier.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRPrinter/IRPrintingPasses.h"
#include "llvm/Passes/OptimizationLevel.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/Debug.h"
#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/FormatVariadic.h"
#include "llvm/Support/Regex.h"
#include "llvm/Target/TargetMachine.h"
#include "llvm/Transforms/AggressiveInstCombine/AggressiveInstCombine.h"
#include "llvm/Transforms/Coroutines/CoroCleanup.h"
#include "llvm/Transforms/Coroutines/CoroConditionalWrapper.h"
#include "llvm/Transforms/Coroutines/CoroEarly.h"
#include "llvm/Transforms/Coroutines/CoroElide.h"
#include "llvm/Transforms/Coroutines/CoroSplit.h"
#include "llvm/Transforms/IPO/AlwaysInliner.h"
#include "llvm/Transforms/IPO/Annotation2Metadata.h"
#include "llvm/Transforms/IPO/ArgumentPromotion.h"
#include "llvm/Transforms/IPO/Attributor.h"
#include "llvm/Transforms/IPO/BlockExtractor.h"
#include "llvm/Transforms/IPO/CalledValuePropagation.h"
#include "llvm/Transforms/IPO/ConstantMerge.h"
#include "llvm/Transforms/IPO/CrossDSOCFI.h"
#include "llvm/Transforms/IPO/DeadArgumentElimination.h"
#include "llvm/Transforms/IPO/ElimAvailExtern.h"
#include "llvm/Transforms/IPO/EmbedBitcodePass.h"
#include "llvm/Transforms/IPO/ForceFunctionAttrs.h"
#include "llvm/Transforms/IPO/FunctionAttrs.h"
#include "llvm/Transforms/IPO/FunctionImport.h"
#include "llvm/Transforms/IPO/GlobalDCE.h"
#include "llvm/Transforms/IPO/GlobalOpt.h"
#include "llvm/Transforms/IPO/GlobalSplit.h"
#include "llvm/Transforms/IPO/HotColdSplitting.h"
#include "llvm/Transforms/IPO/IROutliner.h"
#include "llvm/Transforms/IPO/InferFunctionAttrs.h"
#include "llvm/Transforms/IPO/Inliner.h"
#include "llvm/Transforms/IPO/Internalize.h"
#include "llvm/Transforms/IPO/LoopExtractor.h"
#include "llvm/Transforms/IPO/LowerTypeTests.h"
#include "llvm/Transforms/IPO/MemProfContextDisambiguation.h"
#include "llvm/Transforms/IPO/MergeFunctions.h"
#include "llvm/Transforms/IPO/ModuleInliner.h"
#include "llvm/Transforms/IPO/OpenMPOpt.h"
#include "llvm/Transforms/IPO/PartialInlining.h"
#include "llvm/Transforms/IPO/SCCP.h"
#include "llvm/Transforms/IPO/SampleProfile.h"
#include "llvm/Transforms/IPO/SampleProfileProbe.h"
#include "llvm/Transforms/IPO/StripDeadPrototypes.h"
#include "llvm/Transforms/IPO/StripSymbols.h"
#include "llvm/Transforms/IPO/SyntheticCountsPropagation.h"
#include "llvm/Transforms/IPO/WholeProgramDevirt.h"
#include "llvm/Transforms/InstCombine/InstCombine.h"
#include "llvm/Transforms/Instrumentation.h"
#include "llvm/Transforms/Instrumentation/AddressSanitizer.h"
#include "llvm/Transforms/Instrumentation/BoundsChecking.h"
#include "llvm/Transforms/Instrumentation/CGProfile.h"
#include "llvm/Transforms/Instrumentation/ControlHeightReduction.h"
#include "llvm/Transforms/Instrumentation/DataFlowSanitizer.h"
#include "llvm/Transforms/Instrumentation/GCOVProfiler.h"
#include "llvm/Transforms/Instrumentation/HWAddressSanitizer.h"
#include "llvm/Transforms/Instrumentation/InstrOrderFile.h"
#include "llvm/Transforms/Instrumentation/InstrProfiling.h"
#include "llvm/Transforms/Instrumentation/KCFI.h"
#include "llvm/Transforms/Instrumentation/MemProfiler.h"
#include "llvm/Transforms/Instrumentation/MemorySanitizer.h"
#include "llvm/Transforms/Instrumentation/PGOInstrumentation.h"
#include "llvm/Transforms/Instrumentation/PoisonChecking.h"
#include "llvm/Transforms/Instrumentation/SanitizerBinaryMetadata.h"
#include "llvm/Transforms/Instrumentation/SanitizerCoverage.h"
#include "llvm/Transforms/Instrumentation/ThreadSanitizer.h"
#include "llvm/Transforms/ObjCARC.h"
#include "llvm/Transforms/Scalar/ADCE.h"
#include "llvm/Transforms/Scalar/AlignmentFromAssumptions.h"
#include "llvm/Transforms/Scalar/AnnotationRemarks.h"
#include "llvm/Transforms/Scalar/BDCE.h"
#include "llvm/Transforms/Scalar/CallSiteSplitting.h"
#include "llvm/Transforms/Scalar/ConstantHoisting.h"
#include "llvm/Transforms/Scalar/ConstraintElimination.h"
#include "llvm/Transforms/Scalar/CorrelatedValuePropagation.h"
#include "llvm/Transforms/Scalar/DCE.h"
#include "llvm/Transforms/Scalar/DFAJumpThreading.h"
#include "llvm/Transforms/Scalar/DeadStoreElimination.h"
#include "llvm/Transforms/Scalar/DivRemPairs.h"
#include "llvm/Transforms/Scalar/EarlyCSE.h"
#include "llvm/Transforms/Scalar/FlattenCFG.h"
#include "llvm/Transforms/Scalar/Float2Int.h"
#include "llvm/Transforms/Scalar/GVN.h"
#include "llvm/Transforms/Scalar/GuardWidening.h"
#include "llvm/Transforms/Scalar/IVUsersPrinter.h"
#include "llvm/Transforms/Scalar/IndVarSimplify.h"
#include "llvm/Transforms/Scalar/InductiveRangeCheckElimination.h"
#include "llvm/Transforms/Scalar/InferAddressSpaces.h"
#include "llvm/Transforms/Scalar/InstSimplifyPass.h"
#include "llvm/Transforms/Scalar/JumpThreading.h"
#include "llvm/Transforms/Scalar/LICM.h"
#include "llvm/Transforms/Scalar/LoopAccessAnalysisPrinter.h"
#include "llvm/Transforms/Scalar/LoopBoundSplit.h"
#include "llvm/Transforms/Scalar/LoopDataPrefetch.h"
#include "llvm/Transforms/Scalar/LoopDeletion.h"
#include "llvm/Transforms/Scalar/LoopDistribute.h"
#include "llvm/Transforms/Scalar/LoopFlatten.h"
#include "llvm/Transforms/Scalar/LoopFuse.h"
#include "llvm/Transforms/Scalar/LoopIdiomRecognize.h"
#include "llvm/Transforms/Scalar/LoopInstSimplify.h"
#include "llvm/Transforms/Scalar/LoopInterchange.h"
#include "llvm/Transforms/Scalar/LoopLoadElimination.h"
#include "llvm/Transforms/Scalar/LoopPassManager.h"
#include "llvm/Transforms/Scalar/LoopPredication.h"
#include "llvm/Transforms/Scalar/LoopReroll.h"
#include "llvm/Transforms/Scalar/LoopRotation.h"
#include "llvm/Transforms/Scalar/LoopSimplifyCFG.h"
#include "llvm/Transforms/Scalar/LoopSink.h"
#include "llvm/Transforms/Scalar/LoopStrengthReduce.h"
#include "llvm/Transforms/Scalar/LoopUnrollAndJamPass.h"
#include "llvm/Transforms/Scalar/LoopUnrollPass.h"
#include "llvm/Transforms/Scalar/LoopVersioningLICM.h"
#include "llvm/Transforms/Scalar/LowerAtomicPass.h"
#include "llvm/Transforms/Scalar/LowerConstantIntrinsics.h"
#include "llvm/Transforms/Scalar/LowerExpectIntrinsic.h"
#include "llvm/Transforms/Scalar/LowerGuardIntrinsic.h"
#include "llvm/Transforms/Scalar/LowerMatrixIntrinsics.h"
#include "llvm/Transforms/Scalar/LowerWidenableCondition.h"
#include "llvm/Transforms/Scalar/MakeGuardsExplicit.h"
#include "llvm/Transforms/Scalar/MemCpyOptimizer.h"
#include "llvm/Transforms/Scalar/MergeICmps.h"
#include "llvm/Transforms/Scalar/MergedLoadStoreMotion.h"
#include "llvm/Transforms/Scalar/NaryReassociate.h"
#include "llvm/Transforms/Scalar/NewGVN.h"
#include "llvm/Transforms/Scalar/PartiallyInlineLibCalls.h"
#include "llvm/Transforms/Scalar/PlaceSafepoints.h"
#include "llvm/Transforms/Scalar/Reassociate.h"
#include "llvm/Transforms/Scalar/Reg2Mem.h"
#include "llvm/Transforms/Scalar/RewriteStatepointsForGC.h"
#include "llvm/Transforms/Scalar/SCCP.h"
#include "llvm/Transforms/Scalar/SROA.h"
#include "llvm/Transforms/Scalar/ScalarizeMaskedMemIntrin.h"
#include "llvm/Transforms/Scalar/Scalarizer.h"
#include "llvm/Transforms/Scalar/SeparateConstOffsetFromGEP.h"
#include "llvm/Transforms/Scalar/SimpleLoopUnswitch.h"
#include "llvm/Transforms/Scalar/SimplifyCFG.h"
#include "llvm/Transforms/Scalar/Sink.h"
#include "llvm/Transforms/Scalar/SpeculativeExecution.h"
#include "llvm/Transforms/Scalar/StraightLineStrengthReduce.h"
#include "llvm/Transforms/Scalar/StructurizeCFG.h"
#include "llvm/Transforms/Scalar/TLSVariableHoist.h"
#include "llvm/Transforms/Scalar/TailRecursionElimination.h"
#include "llvm/Transforms/Scalar/WarnMissedTransforms.h"
#include "llvm/Transforms/Utils/AddDiscriminators.h"
#include "llvm/Transforms/Utils/AssumeBundleBuilder.h"
#include "llvm/Transforms/Utils/BreakCriticalEdges.h"
#include "llvm/Transforms/Utils/CanonicalizeAliases.h"
#include "llvm/Transforms/Utils/CanonicalizeFreezeInLoops.h"
#include "llvm/Transforms/Utils/CountVisits.h"
#include "llvm/Transforms/Utils/Debugify.h"
#include "llvm/Transforms/Utils/EntryExitInstrumenter.h"
#include "llvm/Transforms/Utils/FixIrreducible.h"
#include "llvm/Transforms/Utils/HelloWorld.h"
#include "llvm/Transforms/Utils/InjectTLIMappings.h"
#include "llvm/Transforms/Utils/InstructionNamer.h"
#include "llvm/Transforms/Utils/LCSSA.h"
#include "llvm/Transforms/Utils/LibCallsShrinkWrap.h"
#include "llvm/Transforms/Utils/LoopSimplify.h"
#include "llvm/Transforms/Utils/LoopVersioning.h"
#include "llvm/Transforms/Utils/LowerGlobalDtors.h"
#include "llvm/Transforms/Utils/LowerIFunc.h"
#include "llvm/Transforms/Utils/LowerInvoke.h"
#include "llvm/Transforms/Utils/LowerSwitch.h"
#include "llvm/Transforms/Utils/Mem2Reg.h"
#include "llvm/Transforms/Utils/MetaRenamer.h"
#include "llvm/Transforms/Utils/MoveAutoInit.h"
#include "llvm/Transforms/Utils/NameAnonGlobals.h"
#include "llvm/Transforms/Utils/PredicateInfo.h"
#include "llvm/Transforms/Utils/RelLookupTableConverter.h"
#include "llvm/Transforms/Utils/StripGCRelocates.h"
#include "llvm/Transforms/Utils/StripNonLineTableDebugInfo.h"
#include "llvm/Transforms/Utils/SymbolRewriter.h"
#include "llvm/Transforms/Utils/UnifyFunctionExitNodes.h"
#include "llvm/Transforms/Utils/UnifyLoopExits.h"
#include "llvm/Transforms/Vectorize/LoadStoreVectorizer.h"
#include "llvm/Transforms/Vectorize/LoopVectorize.h"
#include "llvm/Transforms/Vectorize/SLPVectorizer.h"
#include "llvm/Transforms/Vectorize/VectorCombine.h"

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
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Transforms/AggressiveInstCombine/AggressiveInstCombine.h>
#include <llvm/Transforms/IPO.h>
#include <llvm/Transforms/IPO/AlwaysInliner.h>
#include <llvm/Transforms/Scalar/SimpleLoopUnswitch.h>
#include <llvm/Transforms/IPO/ArgumentPromotion.h>
#include <llvm/Transforms/Utils.h>
#include <llvm/Transforms/Utils/UnifyFunctionExitNodes.h>

using namespace llvm;

typedef llvm::PassBuilder *LLVMPassBuilder;

typedef llvm::ModulePassManager *LLVMModulePassManager;

typedef llvm::FunctionAnalysisManager *LLVMFunctionAnalysisManager;

typedef llvm::ModuleAnalysisManager *LLVMModuleAnalysisManager;

typedef llvm::PassInstrumentationCallbacks *LLVMPassInstrumentationCallbacks;

typedef llvm::TimePassesHandler *LLVMTimePassesHandler;

/*
 * Exposed API
 */

extern "C" {

API_EXPORT(LLVMTimePassesHandler)
LLVMPY_CreateLLVMTimePassesHandler() { return new TimePassesHandler(true); }

API_EXPORT(void)
LLVMPY_DisposeLLVMTimePassesHandler(LLVMTimePassesHandler TimePasses) {
    delete TimePasses;
}

API_EXPORT(void)
LLVMPY_SetTimePasses(LLVMTimePassesHandler TimePasses,
                     LLVMPassInstrumentationCallbacks PIC) {
    // if (TimePasses)
    //   delete TimePasses;
    // Reset any existing timing
    TimePasses->print();
    TimePasses->registerCallbacks(*PIC);
}

API_EXPORT(void)
LLVMPY_ReportAndResetTimings(LLVMTimePassesHandler TimePasses,
                             const char **outmsg) {
    std::string osbuf;
    raw_string_ostream os(osbuf);
    TimePasses->setOutStream(os);
    TimePasses->print();
    os.flush();
    *outmsg = LLVMPY_CreateString(os.str().c_str());
}

API_EXPORT(LLVMModulePassManager)
LLVMPY_CreatePassManager() { return nullptr; }

API_EXPORT(void)
LLVMPY_DisposePassManager(ModulePassManager *MPM) { delete MPM; }

API_EXPORT(void)
LLVMPY_DisposeFunctionPassManager(FunctionPassManager *FPM) { delete FPM; }

API_EXPORT(FunctionPassManager *)
LLVMPY_CreateFunctionPassManager() { return new FunctionPassManager(); }

API_EXPORT(LoopAnalysisManager *)
LLVMPY_CreateLoopAnalysisManager(LLVMModuleRef M) {
    return new LoopAnalysisManager();
}

API_EXPORT(FunctionAnalysisManager *)
LLVMPY_CreateFunctionAnalysisManager(LLVMModuleRef M) {
    return new FunctionAnalysisManager();
}

API_EXPORT(CGSCCAnalysisManager *)
LLVMPY_CreateCGSCCAnalysisManager(LLVMModuleRef M) {
    return new CGSCCAnalysisManager();
}

API_EXPORT(ModuleAnalysisManager *)
LLVMPY_CreateModuleAnalysisManager(LLVMModuleRef M) {
    return new ModuleAnalysisManager();
}

API_EXPORT(int)
LLVMPY_RunPassManagerWithRemarks(LLVMModulePassManager PM, LLVMModuleRef M,
                                 LLVMModuleAnalysisManager MAM,
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
    auto r = PM->run(*unwrap(M), *MAM);

    unwrap(M)->getContext().setMainRemarkStreamer(nullptr);
    unwrap(M)->getContext().setLLVMRemarkStreamer(nullptr);

    optimisationFile->keep();
    optimisationFile->os().flush();

    // TODO: return void
    return 1;
}

API_EXPORT(int)
LLVMPY_RunPassManager(LLVMModulePassManager PM, LLVMModuleRef M,
                      LLVMModuleAnalysisManager MAM) {
    // PassBuilder PB;
    // LoopAnalysisManager LAM;
    // FunctionAnalysisManager FAM;
    // CGSCCAnalysisManager CGAM;
    // ModuleAnalysisManager MAM;

    // // Register all the basic analyses with the managers.
    // PB.registerModuleAnalyses(MAM);
    // PB.registerCGSCCAnalyses(CGAM);
    // PB.registerFunctionAnalyses(FAM);
    // PB.registerLoopAnalyses(LAM);
    // PB.crossRegisterProxies(LAM, FAM, CGAM, MAM);

    // PM = new
    // llvm::ModulePassManager(PB.buildPerModuleDefaultPipeline(OptimizationLevel::O2,
    // false)); PM->printPipeline(outs(), [](StringRef ClassName) { return
    // ClassName; });
    PM->run(*unwrap(M), *MAM);

    return 0;
}

API_EXPORT(int)
LLVMPY_RunFunctionPassManagerWithRemarks(FunctionPassManager *FPM, Function *F,
                                         LLVMFunctionAnalysisManager FAM,
                                         const char *remarks_format,
                                         const char *remarks_filter,
                                         const char *record_filename) {
    auto setupResult = llvm::setupLLVMOptimizationRemarks(
        F->getContext(), record_filename, remarks_filter, remarks_format, true);
    if (!setupResult) {
        return -1;
    }
    auto optimisationFile = std::move(*setupResult);

    // F->print(outs());
    // FPM->printPipeline(outs(), [](StringRef ClassName) {
    //   return ClassName;
    // });
    FPM->run(*F, *FAM);

    F->getContext().setMainRemarkStreamer(nullptr);
    F->getContext().setLLVMRemarkStreamer(nullptr);

    optimisationFile->keep();
    optimisationFile->os().flush();
    // TODO return void
    return 1;
}

API_EXPORT(int)
LLVMPY_RunFunctionPassManager(FunctionPassManager *FPM, Function *F,
                              LLVMFunctionAnalysisManager FAM) {
    // PassBuilder PB;
    // LoopAnalysisManager LAM;
    // FunctionAnalysisManager FAM;
    // CGSCCAnalysisManager CGAM;
    // ModuleAnalysisManager MAM;

    // // Register all the basic analyses with the managers.
    // PB.registerModuleAnalyses(MAM);
    // PB.registerCGSCCAnalyses(CGAM);
    // PB.registerFunctionAnalyses(FAM);
    // PB.registerLoopAnalyses(LAM);
    // PB.crossRegisterProxies(LAM, FAM, CGAM, MAM);

    // FPM = new
    // llvm::FunctionPassManager(PB.buildFunctionSimplificationPipeline(OptimizationLevel::O2,
    // llvm::ThinOrFullLTOPhase::None)); FPM->printPipeline(outs(), [](StringRef
    // ClassName) { return ClassName; });
    FPM->run(*F, *FAM);

    return 0;
}

// Deprecated, unneeded
API_EXPORT(int)
LLVMPY_InitializeFunctionPassManager(FunctionPassManager *PB) { return 0; }

// Deprecated, unneeded
API_EXPORT(int)
LLVMPY_FinalizeFunctionPassManager(FunctionPassManager *PB) { return 0; }

// TODO register AA passes correctly
API_EXPORT(void)
LLVMPY_AddAAEvalPass(FunctionAnalysisManager *FAM) {
    AAManager AA;
    FAM->registerPass([&] { return std::move(AA); });
}

API_EXPORT(void)
LLVMPY_AddBasicAAWrapperPass(FunctionAnalysisManager *FAM) {
    AAManager AA;
    FAM->registerPass([&] { return std::move(AA); });
}

API_EXPORT(void)
LLVMPY_AddDependenceAnalysisPass(FunctionAnalysisManager *FAM) {
    FAM->registerPass([&] { return DependenceAnalysis(); });
}

API_EXPORT(void)
LLVMPY_AddCallGraphDOTPrinterPass(ModulePassManager *MAM) {
    MAM->addPass(CallGraphDOTPrinterPass());
}

// Not ported over to NPM yet
API_EXPORT(void)
LLVMPY_AddDotDomPrinterPass(LLVMPassManagerRef PM, bool showBody) {
    // #if LLVM_VERSION_MAJOR < 15
    //     unwrap(PM)->add(showBody ? llvm::createDomPrinterPass()
    //                              : llvm::createDomOnlyViewerPass());
    // #else
    //     unwrap(PM)->add(showBody ? llvm::createDomPrinterWrapperPassPass()
    //                              :
    //                              llvm::createDomOnlyViewerWrapperPassPass());
    // #endif
}

API_EXPORT(void)
LLVMPY_AddGlobalsModRefAAPass(ModuleAnalysisManager *MAM) {
    MAM->registerPass([&] { return GlobalsAA(); });
}

// Not ported over to NPM yet
API_EXPORT(void)
LLVMPY_AddDotPostDomPrinterPass(LLVMPassManagerRef PM, bool showBody) {
    // #if LLVM_VERSION_MAJOR < 15
    //     unwrap(PM)->add(showBody ? llvm::createPostDomPrinterPass()
    //                              : llvm::createPostDomOnlyViewerPass());
    // #else
    //     unwrap(PM)->add(showBody ?
    //     llvm::createPostDomPrinterWrapperPassPass()
    //                              :
    //                              llvm::createPostDomOnlyViewerWrapperPassPass());
    // #endif
}

// Not ported over to NPM yet
API_EXPORT(void)
LLVMPY_AddCFGPrinterPass(LLVMPassManagerRef PM) {
    // unwrap(PM)->add(llvm::createCFGPrinterLegacyPassPass());
}

API_EXPORT(void)
LLVMPY_AddConstantMergePass(ModulePassManager *MPM) {
    MPM->addPass(ConstantMergePass());
}

API_EXPORT(void)
LLVMPY_AddDeadStoreEliminationPass(FunctionPassManager *FPM) {
    FPM->addPass(DSEPass());
}

API_EXPORT(void)
LLVMPY_AddReversePostOrderFunctionAttrsPass(ModulePassManager *MPM) {
    MPM->addPass(ReversePostOrderFunctionAttrsPass());
}

API_EXPORT(void)
LLVMPY_AddDeadArgEliminationPass(ModulePassManager *MPM) {
    MPM->addPass(DeadArgumentEliminationPass());
}

// Not ported over to NPM yet
API_EXPORT(void)
LLVMPY_AddInstructionCountPass(LLVMPassManagerRef PM) {
    // unwrap(PM)->add(llvm::createInstCountPass());
}

API_EXPORT(void)
LLVMPY_AddIVUsersPass(LoopAnalysisManager *LAM) {
    LAM->registerPass([&] { return IVUsersAnalysis(); });
}

API_EXPORT(void)
LLVMPY_AddLazyValueInfoPass(FunctionAnalysisManager *FAM) {
    FAM->registerPass([&] { return LazyValueAnalysis(); });
}

API_EXPORT(void)
LLVMPY_AddLintPass(FunctionPassManager *FPM) { FPM->addPass(LintPass()); }

// TODO: does dbgs() work?
API_EXPORT(void)
LLVMPY_AddModuleDebugInfoPrinterPass(ModulePassManager *MPM) {
    MPM->addPass(ModuleDebugInfoPrinterPass(dbgs()));
}

API_EXPORT(void)
LLVMPY_AddRegionInfoPass(FunctionAnalysisManager *FAM) {
    FAM->registerPass([&] { return RegionInfoAnalysis(); });
}

API_EXPORT(void)
LLVMPY_AddScalarEvolutionAAPass(FunctionAnalysisManager *FAM) {
    FAM->registerPass([&] { return SCEVAA(); });
}

API_EXPORT(void)
LLVMPY_AddAggressiveDCEPass(FunctionPassManager *FPM) {
    FPM->addPass(ADCEPass());
}

API_EXPORT(void)
LLVMPY_AddAlwaysInlinerPass(ModulePassManager *MPM, bool insertLifetime) {
    MPM->addPass(AlwaysInlinerPass(insertLifetime));
}

API_EXPORT(void)
LLVMPY_AddArgPromotionPass(ModulePassManager *MPM, unsigned int maxElements) {
    MPM->addPass(
        createModuleToPostOrderCGSCCPassAdaptor(ArgumentPromotionPass()));
}

API_EXPORT(void)
LLVMPY_AddBreakCriticalEdgesPass(FunctionPassManager *FPM) {
    FPM->addPass(BreakCriticalEdgesPass());
}

API_EXPORT(void)
LLVMPY_AddFunctionAttrsPass(LLVMPassManagerRef PM) {
    assert(false && "FunctionAttrsPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddFunctionInliningPass(LLVMModulePassManager MPM, int Threshold) {
    MPM->addPass(ModuleInlinerWrapperPass(getInlineParams(Threshold)));
}

API_EXPORT(void)
LLVMPY_AddGlobalOptimizerPass(LLVMPassManagerRef PM) {
    assert(false && "GlobalOptimizerPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddGlobalDCEPass(LLVMPassManagerRef PM) {
    assert(false && "GlobalDCEPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddIPSCCPPass(LLVMPassManagerRef PM) {
    assert(false && "IPSCCPPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddDeadCodeEliminationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createDeadCodeEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddAggressiveInstructionCombiningPass(LLVMPassManagerRef PM) {
    assert(false && "AggressiveInstructionCombiningPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddInternalizePass(LLVMPassManagerRef PM) {
    assert(false && "InternalizePass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddJumpThreadingPass(LLVMPassManagerRef PM, int threshold) {
    assert(false && "JumpThreadingPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddLCSSAPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createLCSSAPass());
}

API_EXPORT(void)
LLVMPY_AddLoopDeletionPass(LLVMPassManagerRef PM) {
    assert(false && "LoopDeletionPass is Legacy");
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
LLVMPY_AddLoopUnrollPass(LLVMPassManagerRef PM) {
    assert(false && "LoopUnrollPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddLoopUnrollAndJamPass(LLVMPassManagerRef PM) {
    assert(false && "LoopUnrollAndJamPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddLoopUnswitchPass(LLVMPassManagerRef PM, bool optimizeForSize,
                           bool hasBranchDivergence) {
#if LLVM_VERSION_MAJOR < 15
    unwrap(PM)->add(
        createLoopUnswitchPass(optimizeForSize, hasBranchDivergence));
#else
    unwrap(PM)->add(createSimpleLoopUnswitchLegacyPass(optimizeForSize));
#endif
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
    assert(false && "MemCpyOptimizationPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddMergeFunctionsPass(LLVMPassManagerRef PM) {
    assert(false && "MergeFunctionsPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddMergeReturnsPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createUnifyFunctionExitNodesPass());
}

API_EXPORT(void)
LLVMPY_AddPartialInliningPass(LLVMPassManagerRef PM) {
    assert(false && "PartialInliningPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddPruneExceptionHandlingPass(LLVMPassManagerRef PM) {
    assert(false && "PruneExceptionHandlingPass is Legacy");
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
    assert(false && "StripSymbolsPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddStripDeadDebugInfoPass(LLVMPassManagerRef PM) {
    assert(false && "StripDeadDebugInfoPass( is Legacy");
}

API_EXPORT(void)
LLVMPY_AddStripDeadPrototypesPass(LLVMPassManagerRef PM) {
    assert(false && "StripDeadPrototypesPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddStripDebugDeclarePrototypesPass(LLVMPassManagerRef PM) {
    assert(false && "StripDebugDeclarePrototypesPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddStripNondebugSymbolsPass(LLVMPassManagerRef PM) {
    assert(false && "StripNondebugSymbolsPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddTailCallEliminationPass(LLVMPassManagerRef PM) {
    unwrap(PM)->add(createTailCallEliminationPass());
}

API_EXPORT(void)
LLVMPY_AddCFGSimplificationPass(LLVMPassManagerRef PM) {
    assert(false && "CFGSimplificationPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddGVNPass(LLVMPassManagerRef PM) {
    assert(false && "GVNPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddInstructionCombiningPass(ModulePassManager *PM) {
    PM->addPass(createModuleToFunctionPassAdaptor(InstCombinePass()));
}

API_EXPORT(void)
LLVMPY_AddLICMPass(FunctionPassManager *PM) {
    PM->addPass(createFunctionToLoopPassAdaptor(
        LICMPass(/*PTO.LicmMssaOptCap=*/SetLicmMssaOptCap,
                 /*PTO.LicmMssaNoAccForPromotionCap=*/
                 SetLicmMssaNoAccForPromotionCap,
                 /*AllowSpeculation=*/true),
        /*UseMemorySSA=*/true, /*UseBlockFrequencyInfo=*/true));
}

API_EXPORT(void)
LLVMPY_AddSCCPPass(LLVMPassManagerRef PM) {
    assert(false && "SCCPPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddSROAPass(LLVMPassManagerRef PM) { unwrap(PM)->add(createSROAPass()); }

API_EXPORT(void)
LLVMPY_AddTypeBasedAliasAnalysisPass(LLVMPassManagerRef PM) {
    assert(false && "TypeBasedAliasAnalysisPass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddBasicAliasAnalysisPass(LLVMPassManagerRef PM) {
    assert(false && "BasicAliasAnalysisPass is Legacy");
}

API_EXPORT(void)
LLVMPY_LLVMAddLoopRotatePass(LLVMPassManagerRef PM) {
    assert(false && "AddLoopRotatePass is Legacy");
}

API_EXPORT(void)
LLVMPY_AddInstructionNamerPass(LLVMModulePassManager PM) {
    PM->addPass(createModuleToFunctionPassAdaptor(InstructionNamerPass()));
}

} // end extern "C"
