#include "core.h"
#include "llvm-c/TargetMachine.h"
#include "llvm/Analysis/AliasAnalysisEvaluator.h"
#include "llvm/Analysis/AliasSetTracker.h"
#include "llvm/Analysis/AssumptionCache.h"
#include "llvm/Analysis/BasicAliasAnalysis.h"
#include "llvm/Analysis/BlockFrequencyInfo.h"
#include "llvm/Analysis/BranchProbabilityInfo.h"
#include "llvm/Analysis/CFGPrinter.h"
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
#include "llvm/IR/Dominators.h"
#include "llvm/IR/IRPrintingPasses.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/StandardInstrumentations.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/AggressiveInstCombine/AggressiveInstCombine.h"
#include "llvm/Transforms/Coroutines/CoroCleanup.h"
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
#include "llvm/Transforms/IPO/MergeFunctions.h"
#include "llvm/Transforms/IPO/ModuleInliner.h"
#include "llvm/Transforms/IPO/OpenMPOpt.h"
#include "llvm/Transforms/IPO/PartialInlining.h"
#include "llvm/Transforms/IPO/SCCP.h"
#include "llvm/Transforms/IPO/SampleProfile.h"
#include "llvm/Transforms/IPO/SampleProfileProbe.h"
#include "llvm/Transforms/IPO/StripDeadPrototypes.h"
#include "llvm/Transforms/IPO/StripSymbols.h"
#include "llvm/Transforms/IPO/WholeProgramDevirt.h"
#include "llvm/Transforms/InstCombine/InstCombine.h"
#include "llvm/Transforms/Instrumentation/AddressSanitizer.h"
#include "llvm/Transforms/Instrumentation/BoundsChecking.h"
#include "llvm/Transforms/Instrumentation/CGProfile.h"
#include "llvm/Transforms/Instrumentation/ControlHeightReduction.h"
#include "llvm/Transforms/Instrumentation/DataFlowSanitizer.h"
#include "llvm/Transforms/Instrumentation/GCOVProfiler.h"
#include "llvm/Transforms/Instrumentation/HWAddressSanitizer.h"
#include "llvm/Transforms/Instrumentation/InstrOrderFile.h"
#include "llvm/Transforms/Instrumentation/InstrProfiling.h"
#include "llvm/Transforms/Instrumentation/MemProfiler.h"
#include "llvm/Transforms/Instrumentation/MemorySanitizer.h"
#include "llvm/Transforms/Instrumentation/PGOInstrumentation.h"
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
#include "llvm/Transforms/Scalar/TailRecursionElimination.h"
#include "llvm/Transforms/Scalar/WarnMissedTransforms.h"
#include "llvm/Transforms/Utils/AddDiscriminators.h"
#include "llvm/Transforms/Utils/AssumeBundleBuilder.h"
#include "llvm/Transforms/Utils/BreakCriticalEdges.h"
#include "llvm/Transforms/Utils/CanonicalizeAliases.h"
#include "llvm/Transforms/Utils/CanonicalizeFreezeInLoops.h"
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
#include "llvm/Transforms/Utils/LowerInvoke.h"
#include "llvm/Transforms/Utils/LowerSwitch.h"
#include "llvm/Transforms/Utils/Mem2Reg.h"
#include "llvm/Transforms/Utils/MetaRenamer.h"
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
#include <llvm/IR/PassTimingInfo.h>

using namespace llvm;

#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)

/*
 * Exposed API
 */

namespace llvm {

struct OpaqueModulePassManager;
typedef OpaqueModulePassManager *LLVMModulePassManagerRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(ModulePassManager, LLVMModulePassManagerRef)

struct OpaqueFunctionPassManager;
typedef OpaqueFunctionPassManager *LLVMFunctionPassManagerRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(FunctionPassManager,
                                   LLVMFunctionPassManagerRef)

struct OpaquePassBuilder;
typedef OpaquePassBuilder *LLVMPassBuilderRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(PassBuilder, LLVMPassBuilderRef)

struct OpaquePipelineTuningOptions;
typedef OpaquePipelineTuningOptions *LLVMPipelineTuningOptionsRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(PipelineTuningOptions,
                                   LLVMPipelineTuningOptionsRef)

struct OpaqueTimePassesHandler;
typedef OpaqueTimePassesHandler *LLVMTimePassesHandlerRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(TimePassesHandler, LLVMTimePassesHandlerRef)

static TargetMachine *unwrap(LLVMTargetMachineRef P) {
    return reinterpret_cast<TargetMachine *>(P);
}

} // namespace llvm

// C++ linkage
static OptimizationLevel mapLevel(int speed_level, int size_level) {
    switch (size_level) {
    case 0:
        switch (speed_level) {
        case 0:
            return OptimizationLevel::O0;
        case 1:
            return OptimizationLevel::O1;
        case 2:
            return OptimizationLevel::O2;
        case 3:
            return OptimizationLevel::O3;
        default:
            llvm_unreachable("Invalid optimization level");
        }
    case 1:
        if (speed_level == 1)
            return OptimizationLevel::Os;
        llvm_unreachable("Invalid optimization level for size level 1");
    case 2:
        if (speed_level == 2)
            return OptimizationLevel::Oz;
        llvm_unreachable("Invalid optimization level for size level 2");
    default:
        llvm_unreachable("Invalid size level");
        break;
    }
}

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

// MPM

API_EXPORT(LLVMModulePassManagerRef)
LLVMPY_CreateNewModulePassManager() {
    return llvm::wrap(new PassManager<Module>());
}

API_EXPORT(void)
LLVMPY_RunNewModulePassManager(LLVMModulePassManagerRef MPMRef,
                               LLVMModuleRef mod, LLVMPassBuilderRef PBRef) {

    ModulePassManager *MPM = llvm::unwrap(MPMRef);
    Module *M = llvm::unwrap(mod);
    PassBuilder *PB = llvm::unwrap(PBRef);

    // TODO: Make these set(able) by user
    bool DebugLogging = false;
    bool VerifyEach = false;

    LoopAnalysisManager LAM;
    FunctionAnalysisManager FAM;
    CGSCCAnalysisManager CGAM;
    ModuleAnalysisManager MAM;

    PrintPassOptions PrintPassOpts;

    // NOTE: The following are used to provide an alternative outstream to
    // STDOUT and need to be declared ahead of instantiating the
    // StandardInstrumentations instance as they need to have a lifetime that
    // is longer than the StandardInstrumentations. See following notes for
    // details:
    //
    // The reason for this is that a StandardInstrumentations instance (SI)
    // contains a TimePassesHandler instance (TP), when the SI goes out of scope
    // it triggers the TP member destructor, and this is defined so as to call
    // `TP->print()` to trigger the side effect of draining the pass timing
    // buffer and resetting the timers. This `print()` call will by default
    // drain to stdout and so a buffer is provided in the following and set as
    // the "out stream" for the TP so that any such printing isn't visible to
    // the user. Independently of all this, if the user wants timing
    // information, there is a managed TP instance along with code managing the
    // state of information capturing available as part of the LLVMPY interface.
    // This is independently registered and managed outside of the
    // StandardInstrumentations system.
    //
    // Summary: the StandardInstrumentations TimePassesHandler instance isn't
    // used by anything available to llvmlite users, and so its printing stuff
    // is just being hidden.
    std::string osbuf;
    raw_string_ostream os(osbuf);

    StandardInstrumentations SI(M->getContext(), DebugLogging, VerifyEach,
                                PrintPassOpts);

    // https://reviews.llvm.org/D146160
    SI.registerCallbacks(*PB->getPassInstrumentationCallbacks(), &MAM);

    // If the timing information is required, this is handled elsewhere, the
    // instance of the TimePassesHandler on the StandardInstrumentations object
    // needs to just redirect its print output to somewhere not visible to
    // users.
    if (TimePassesIsEnabled) {
        TimePassesHandler &TP = SI.getTimePasses();
        TP.setOutStream(os);
    }

    PB->registerLoopAnalyses(LAM);
    PB->registerFunctionAnalyses(FAM);
    PB->registerCGSCCAnalyses(CGAM);
    PB->registerModuleAnalyses(MAM);
    PB->crossRegisterProxies(LAM, FAM, CGAM, MAM);

    MPM->run(*M, MAM);
}

API_EXPORT(void)
LLVMPY_AddJumpThreadingPass_module(LLVMModulePassManagerRef MPM, int T) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(JumpThreadingPass(T)));
}

API_EXPORT(void)
LLVMPY_DisposeNewModulePassManger(LLVMModulePassManagerRef MPM) {
    delete llvm::unwrap(MPM);
}

// FPM

API_EXPORT(LLVMFunctionPassManagerRef)
LLVMPY_CreateNewFunctionPassManager() {
    return llvm::wrap(new PassManager<Function>());
}

API_EXPORT(void)
LLVMPY_RunNewFunctionPassManager(LLVMFunctionPassManagerRef FPMRef,
                                 LLVMValueRef FRef, LLVMPassBuilderRef PBRef) {

    FunctionPassManager *FPM = llvm::unwrap(FPMRef);
    Function *F = reinterpret_cast<Function *>(FRef);
    PassBuilder *PB = llvm::unwrap(PBRef);

    // Don't try to optimize function declarations
    if (F->isDeclaration())
        return;

    // TODO: Make these set(able) by user
    bool DebugLogging = false;
    bool VerifyEach = false;

    LoopAnalysisManager LAM;
    FunctionAnalysisManager FAM;
    CGSCCAnalysisManager CGAM;
    ModuleAnalysisManager MAM;

    // TODO: Can expose this in ffi layer
    PrintPassOptions PrintPassOpts;

    // See note in LLVMPY_RunNewModulePassManager for what is going on with
    // these variables and the call below to TP.setOutStream().
    std::string osbuf;
    raw_string_ostream os(osbuf);

    StandardInstrumentations SI(F->getContext(), DebugLogging, VerifyEach,
                                PrintPassOpts);

    // https://reviews.llvm.org/D146160
    SI.registerCallbacks(*PB->getPassInstrumentationCallbacks(), &MAM);

    if (TimePassesIsEnabled) {
        TimePassesHandler &TP = SI.getTimePasses();
        TP.setOutStream(os);
    }

    PB->registerLoopAnalyses(LAM);
    PB->registerFunctionAnalyses(FAM);
    PB->registerCGSCCAnalyses(CGAM);
    PB->registerModuleAnalyses(MAM);
    PB->crossRegisterProxies(LAM, FAM, CGAM, MAM);
    FPM->run(*F, FAM);
}

API_EXPORT(void)
LLVMPY_AddJumpThreadingPass_function(LLVMFunctionPassManagerRef FPM, int T) {
    llvm::unwrap(FPM)->addPass(JumpThreadingPass(T));
}

API_EXPORT(void)
LLVMPY_DisposeNewFunctionPassManger(LLVMFunctionPassManagerRef FPM) {
    delete llvm::unwrap(FPM);
}

// PTO

API_EXPORT(LLVMPipelineTuningOptionsRef)
LLVMPY_CreatePipelineTuningOptions() {
    return llvm::wrap(new PipelineTuningOptions());
}

API_EXPORT(bool)
LLVMPY_PTOGetLoopInterleaving(LLVMPipelineTuningOptionsRef PTO) {
    return llvm::unwrap(PTO)->LoopInterleaving;
}

API_EXPORT(void)
LLVMPY_PTOSetLoopInterleaving(LLVMPipelineTuningOptionsRef PTO, bool value) {
    llvm::unwrap(PTO)->LoopInterleaving = value;
}

API_EXPORT(bool)
LLVMPY_PTOGetLoopVectorization(LLVMPipelineTuningOptionsRef PTO) {
    return llvm::unwrap(PTO)->LoopVectorization;
}

API_EXPORT(void)
LLVMPY_PTOSetLoopVectorization(LLVMPipelineTuningOptionsRef PTO, bool value) {
    llvm::unwrap(PTO)->LoopVectorization = value;
}

API_EXPORT(bool)
LLVMPY_PTOGetSLPVectorization(LLVMPipelineTuningOptionsRef PTO) {
    return llvm::unwrap(PTO)->SLPVectorization;
}

API_EXPORT(void)
LLVMPY_PTOSetSLPVectorization(LLVMPipelineTuningOptionsRef PTO, bool value) {
    llvm::unwrap(PTO)->SLPVectorization = value;
}

API_EXPORT(bool)
LLVMPY_PTOGetLoopUnrolling(LLVMPipelineTuningOptionsRef PTO) {
    return llvm::unwrap(PTO)->LoopUnrolling;
}

API_EXPORT(void)
LLVMPY_PTOSetLoopUnrolling(LLVMPipelineTuningOptionsRef PTO, bool value) {
    llvm::unwrap(PTO)->LoopUnrolling = value;
}

API_EXPORT(int)
LLVMPY_PTOGetInlinerThreshold(LLVMPipelineTuningOptionsRef PTO) {
    return llvm::unwrap(PTO)->InlinerThreshold;
}

API_EXPORT(void)
LLVMPY_PTOSetInlinerThreshold(LLVMPipelineTuningOptionsRef PTO, bool value) {
    llvm::unwrap(PTO)->InlinerThreshold = value;
}

API_EXPORT(void)
LLVMPY_DisposePipelineTuningOptions(LLVMPipelineTuningOptionsRef PTO) {
    delete llvm::unwrap(PTO);
}

// PB

API_EXPORT(LLVMTimePassesHandlerRef)
LLVMPY_CreateTimePassesHandler() {
    bool enabled = true;
    return llvm::wrap(new TimePassesHandler(enabled));
}

API_EXPORT(void)
LLVMPY_DisposeTimePassesHandler(LLVMTimePassesHandlerRef TimePassesRef) {
    delete llvm::unwrap(TimePassesRef);
}

API_EXPORT(void)
LLVMPY_EnableTimePasses(LLVMPassBuilderRef PBRef,
                        LLVMTimePassesHandlerRef TimePassesRef) {
    TimePassesHandler *TP = llvm::unwrap(TimePassesRef);
    TimePassesIsEnabled = true;
    PassBuilder *PB = llvm::unwrap(PBRef);
    PassInstrumentationCallbacks *PIC = PB->getPassInstrumentationCallbacks();
    TP->registerCallbacks(*PIC);
}

API_EXPORT(void)
LLVMPY_ReportAndDisableTimePasses(LLVMTimePassesHandlerRef TimePassesRef,
                                  const char **outmsg) {
    std::string osbuf;
    raw_string_ostream os(osbuf);
    TimePassesHandler *TP = llvm::unwrap(TimePassesRef);
    TP->setOutStream(os);
    TP->print();
    os.flush();
    *outmsg = LLVMPY_CreateString(os.str().c_str());
    TimePassesIsEnabled = false;
}

API_EXPORT(LLVMPassBuilderRef)
LLVMPY_CreatePassBuilder(LLVMTargetMachineRef TMRef,
                         LLVMPipelineTuningOptionsRef PTORef) {
    TargetMachine *TM = llvm::unwrap(TMRef);
    PipelineTuningOptions *PTO = llvm::unwrap(PTORef);
    PassInstrumentationCallbacks *PIC = new PassInstrumentationCallbacks();
    return llvm::wrap(new PassBuilder(TM, *PTO, std::nullopt, PIC));
}

API_EXPORT(void)
LLVMPY_DisposePassBuilder(LLVMPassBuilderRef PBRef) {
    delete llvm::unwrap(PBRef);
}

API_EXPORT(LLVMModulePassManagerRef)
LLVMPY_buildPerModuleDefaultPipeline(LLVMPassBuilderRef PBref, int speed_level,
                                     int size_level) {

    PassBuilder *PB = llvm::unwrap(PBref);
    OptimizationLevel OL = mapLevel(speed_level, size_level);

    // FIXME: No need to explicitly take care of O0 from LLVM 17
    if (OL == OptimizationLevel::O0) {
        return llvm::wrap(
            new ModulePassManager(PB->buildO0DefaultPipeline(OL)));
    }

    return llvm::wrap(
        new ModulePassManager(PB->buildPerModuleDefaultPipeline(OL)));
}

API_EXPORT(LLVMFunctionPassManagerRef)
LLVMPY_buildFunctionSimplificationPipeline(LLVMPassBuilderRef PBref,
                                           int speed_level, int size_level) {

    PassBuilder *PB = llvm::unwrap(PBref);
    OptimizationLevel OL = mapLevel(speed_level, size_level);
    if (OL == OptimizationLevel::O0)
        return llvm::wrap(new FunctionPassManager());

    FunctionPassManager *FPM = new FunctionPassManager(
        PB->buildFunctionSimplificationPipeline(OL, ThinOrFullLTOPhase::None));
    return llvm::wrap(FPM);
}

// TODO: From LLVM 16 SROA takes parameter whether to preserve cfg or not which
// can be exposed in the Python API https://reviews.llvm.org/D138238
API_EXPORT(void)
LLVMPY_module_AddSROAPass(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(SROAPass(SROAOptions::PreserveCFG)));
}

API_EXPORT(void)
LLVMPY_function_AddSROAPass(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(SROAPass(SROAOptions::PreserveCFG));
}

API_EXPORT(void)
LLVMPY_module_AddModuleDebugInfoPrinterPass(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(ModuleDebugInfoPrinterPass(llvm::outs()));
}

#define CGSCC_PASS(NAME)                                                       \
    API_EXPORT(void) LLVMPY_module_Add##NAME(LLVMModulePassManagerRef MPM) {   \
        llvm::unwrap(MPM)->addPass(                                            \
            createModuleToPostOrderCGSCCPassAdaptor(NAME()));                  \
    }
#include "PASSREGISTRY.def"

#define MODULE_PASS(NAME)                                                      \
    API_EXPORT(void) LLVMPY_module_Add##NAME(LLVMModulePassManagerRef MPM) {   \
        llvm::unwrap(MPM)->addPass(NAME());                                    \
    }
#include "PASSREGISTRY.def"

#define FUNCTION_PASS(NAME)                                                    \
    API_EXPORT(void) LLVMPY_module_Add##NAME(LLVMModulePassManagerRef MPM) {   \
        llvm::unwrap(MPM)->addPass(createModuleToFunctionPassAdaptor(NAME())); \
    }                                                                          \
    API_EXPORT(void)                                                           \
    LLVMPY_function_Add##NAME(LLVMFunctionPassManagerRef FPM) {                \
        llvm::unwrap(FPM)->addPass(NAME());                                    \
    }
#include "PASSREGISTRY.def"

#define LOOP_PASS(NAME)                                                        \
    API_EXPORT(void) LLVMPY_module_Add##NAME(LLVMModulePassManagerRef MPM) {   \
        llvm::unwrap(MPM)->addPass(createModuleToFunctionPassAdaptor(          \
            createFunctionToLoopPassAdaptor(NAME())));                         \
    }                                                                          \
    API_EXPORT(void)                                                           \
    LLVMPY_function_Add##NAME(LLVMFunctionPassManagerRef FPM) {                \
        llvm::unwrap(FPM)->addPass(createFunctionToLoopPassAdaptor(NAME()));   \
    }
#include "PASSREGISTRY.def"

} // end extern "C"
