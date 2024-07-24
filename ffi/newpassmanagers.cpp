#include "core.h"
#include "llvm-c/TargetMachine.h"
#include "llvm/Analysis/AliasAnalysisEvaluator.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/StandardInstrumentations.h"
#include "llvm/Transforms/InstCombine/InstCombine.h"
#include "llvm/Transforms/Scalar/JumpThreading.h"
#include "llvm/Transforms/Scalar/LoopRotation.h"
#include "llvm/Transforms/Scalar/LoopUnrollPass.h"
#include "llvm/Transforms/Scalar/SimplifyCFG.h"

using namespace llvm;

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

static TargetMachine *unwrap(LLVMTargetMachineRef P) {
    return reinterpret_cast<TargetMachine *>(P);
}

} // namespace llvm

extern "C" {

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

#if LLVM_VERSION_MAJOR < 16
    StandardInstrumentations SI(DebugLogging, VerifyEach, PrintPassOpts);
#else
    StandardInstrumentations SI(M->getContext(), DebugLogging, VerifyEach,
                                PrintPassOpts);
#endif
    SI.registerCallbacks(*PB->getPassInstrumentationCallbacks(), &FAM);

    PB->registerLoopAnalyses(LAM);
    PB->registerFunctionAnalyses(FAM);
    PB->registerCGSCCAnalyses(CGAM);
    PB->registerModuleAnalyses(MAM);
    PB->crossRegisterProxies(LAM, FAM, CGAM, MAM);
    MPM->run(*M, MAM);
}

API_EXPORT(void)
LLVMPY_AddVerifierPass(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(VerifierPass());
}

API_EXPORT(void)
LLVMPY_AddAAEvalPass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(AAEvaluator()));
}

API_EXPORT(void)
LLVMPY_AddSimplifyCFGPass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(SimplifyCFGPass()));
}

API_EXPORT(void)
LLVMPY_AddLoopUnrollPass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(LoopUnrollPass()));
}

API_EXPORT(void)
LLVMPY_AddLoopRotatePass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(createModuleToFunctionPassAdaptor(
        createFunctionToLoopPassAdaptor(LoopRotatePass())));
}

API_EXPORT(void)
LLVMPY_AddInstructionCombinePass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(InstCombinePass()));
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

#if LLVM_VERSION_MAJOR < 16
    StandardInstrumentations SI(DebugLogging, VerifyEach, PrintPassOpts);
#else
    StandardInstrumentations SI(F->getContext(), DebugLogging, VerifyEach,
                                PrintPassOpts);
#endif
    SI.registerCallbacks(*PB->getPassInstrumentationCallbacks(), &FAM);

    PB->registerLoopAnalyses(LAM);
    PB->registerFunctionAnalyses(FAM);
    PB->registerCGSCCAnalyses(CGAM);
    PB->registerModuleAnalyses(MAM);
    PB->crossRegisterProxies(LAM, FAM, CGAM, MAM);
    FPM->run(*F, FAM);
}

API_EXPORT(void)
LLVMPY_AddAAEvalPass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(AAEvaluator());
}

API_EXPORT(void)
LLVMPY_AddSimplifyCFGPass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(SimplifyCFGPass());
}

API_EXPORT(void)
LLVMPY_AddLoopUnrollPass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(LoopUnrollPass());
}

API_EXPORT(void)
LLVMPY_AddLoopRotatePass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(
        createFunctionToLoopPassAdaptor(LoopRotatePass()));
}

API_EXPORT(void)
LLVMPY_AddInstructionCombinePass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(InstCombinePass());
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

// FIXME: Available from llvm16
// API_EXPORT(int)
// LLVMPY_PTOGetInlinerThreshold(LLVMPipelineTuningOptionsRef PTO) {
//     return llvm::unwrap(PTO)->InlinerThreshold;
// }

// API_EXPORT(void)
// LLVMPY_PTOSetInlinerThreshold(LLVMPipelineTuningOptionsRef PTO, bool value) {
//     llvm::unwrap(PTO)->InlinerThreshold = value;
// }

API_EXPORT(void)
LLVMPY_DisposePipelineTuningOptions(LLVMPipelineTuningOptionsRef PTO) {
    delete llvm::unwrap(PTO);
}

// PB

API_EXPORT(LLVMPassBuilderRef)
LLVMPY_CreatePassBuilder(LLVMTargetMachineRef TM,
                         LLVMPipelineTuningOptionsRef PTO) {
    TargetMachine *target = llvm::unwrap(TM);
    PipelineTuningOptions *pt = llvm::unwrap(PTO);
    PassInstrumentationCallbacks *PIC = new PassInstrumentationCallbacks();
#if LLVM_VERSION_MAJOR < 16
    return llvm::wrap(new PassBuilder(target, *pt, None, PIC));
#else
    return llvm::wrap(new PassBuilder(target, *pt, std::nullopt, PIC));
#endif
}

API_EXPORT(void)
LLVMPY_DisposePassBuilder(LLVMPassBuilderRef PB) { delete llvm::unwrap(PB); }

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

} // end extern "C"
