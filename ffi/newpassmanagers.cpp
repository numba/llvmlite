#include "core.h"
#include "llvm-c/TargetMachine.h"
#include "llvm/Analysis/AliasAnalysisEvaluator.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Passes/PassBuilder.h"
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

// TODO: Use DEFINE_SIMPLE_CONVERSION_FUNCTIONS llvm macro
struct OpaqueModulePassManager;
typedef OpaqueModulePassManager *LLVMModulePassManagerRef;

static LLVMModulePassManagerRef wrap(ModulePassManager *MPM) {
    return reinterpret_cast<LLVMModulePassManagerRef>(MPM);
}

static ModulePassManager *unwrap(LLVMModulePassManagerRef MPM) {
    return reinterpret_cast<ModulePassManager *>(MPM);
}

struct OpaqueFunctionPassManager;
typedef OpaqueFunctionPassManager *LLVMFunctionPassManagerRef;

static LLVMFunctionPassManagerRef wrap(FunctionPassManager *FPM) {
    return reinterpret_cast<LLVMFunctionPassManagerRef>(FPM);
}

static FunctionPassManager *unwrap(LLVMFunctionPassManagerRef FPM) {
    return reinterpret_cast<FunctionPassManager *>(FPM);
}

struct OpaquePassBuilder;
typedef OpaquePassBuilder *LLVMPassBuilderRef;

static LLVMPassBuilderRef wrap(PassBuilder *FPM) {
    return reinterpret_cast<LLVMPassBuilderRef>(FPM);
}

static PassBuilder *unwrap(LLVMPassBuilderRef FPM) {
    return reinterpret_cast<PassBuilder *>(FPM);
}

struct OpaquePipelineTuningOptions;
typedef OpaquePipelineTuningOptions *LLVMPipelineTuningOptionsRef;

static LLVMPipelineTuningOptionsRef wrap(PipelineTuningOptions *PTO) {
    return reinterpret_cast<LLVMPipelineTuningOptionsRef>(PTO);
}

static PipelineTuningOptions *unwrap(LLVMPipelineTuningOptionsRef PTO) {
    return reinterpret_cast<PipelineTuningOptions *>(PTO);
}

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
LLVMPY_NMPRun_module(LLVMModulePassManagerRef MPMRef, LLVMPassBuilderRef PBRef,
                     LLVMModuleRef mod) {

    ModulePassManager *MPM = llvm::unwrap(MPMRef);
    PassBuilder *PB = llvm::unwrap(PBRef);
    Module *M = llvm::unwrap(mod);

    LoopAnalysisManager LAM;
    FunctionAnalysisManager FAM;
    CGSCCAnalysisManager CGAM;
    ModuleAnalysisManager MAM;
    PB->registerLoopAnalyses(LAM);
    PB->registerFunctionAnalyses(FAM);
    PB->registerCGSCCAnalyses(CGAM);
    PB->registerModuleAnalyses(MAM);
    PB->crossRegisterProxies(LAM, FAM, CGAM, MAM);
    MPM->run(*M, MAM);
}

API_EXPORT(void)
LLVMPY_AddVeriferPass(LLVMModulePassManagerRef MPM) {
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
LLVMPY_LLVMAddLoopRotatePass_module(LLVMModulePassManagerRef MPM) {
    llvm::unwrap(MPM)->addPass(createModuleToFunctionPassAdaptor(
        createFunctionToLoopPassAdaptor(LoopRotatePass())));
}

API_EXPORT(void)
LLVMPY_LLVMAddInstructionCombinePass_module(LLVMModulePassManagerRef MPM) {
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
LLVMPY_NMPRun_function(LLVMFunctionPassManagerRef FPMRef,
                       LLVMPassBuilderRef PBRef, LLVMValueRef FRef) {

    FunctionPassManager *FPM = llvm::unwrap(FPMRef);
    PassBuilder *PB = llvm::unwrap(PBRef);
    Function *F = reinterpret_cast<Function *>(FRef);

    LoopAnalysisManager LAM;
    FunctionAnalysisManager FAM;
    CGSCCAnalysisManager CGAM;
    ModuleAnalysisManager MAM;
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
LLVMPY_LLVMAddLoopRotatePass_function(LLVMFunctionPassManagerRef FPM) {
    llvm::unwrap(FPM)->addPass(
        createFunctionToLoopPassAdaptor(LoopRotatePass()));
}

API_EXPORT(void)
LLVMPY_LLVMAddInstructionCombinePass_function(LLVMFunctionPassManagerRef FPM) {
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
    return llvm::wrap(new PassBuilder(target, *pt));
}

API_EXPORT(LLVMModulePassManagerRef)
LLVMPY_buildPerModuleDefaultPipeline(LLVMPassBuilderRef PBref, int opt_level) {

    PassBuilder *PB = llvm::unwrap(PBref);
    ModulePassManager *MPM;
    if (opt_level == 0) {
        MPM = new ModulePassManager(
            PB->buildO0DefaultPipeline(OptimizationLevel::O0));
        return llvm::wrap(MPM);
    }

    OptimizationLevel lvl;
    if (opt_level == 1)
        lvl = OptimizationLevel::O1;
    else if (opt_level == 2)
        lvl = OptimizationLevel::O2;
    else
        lvl = OptimizationLevel::O3;

    MPM = new ModulePassManager(PB->buildPerModuleDefaultPipeline(lvl));
    return llvm::wrap(MPM);
}

API_EXPORT(LLVMFunctionPassManagerRef)
LLVMPY_buildFunctionSimplificationPipeline(LLVMPassBuilderRef PBref,
                                           int opt_level) {

    PassBuilder *PB = llvm::unwrap(PBref);
    FunctionPassManager *FPM;
    if (opt_level == 0) {
        FPM = new FunctionPassManager();
        return llvm::wrap(FPM);
    }

    OptimizationLevel lvl;
    if (opt_level == 1)
        lvl = OptimizationLevel::O1;
    else if (opt_level == 2)
        lvl = OptimizationLevel::O2;
    else
        lvl = OptimizationLevel::O3;

    FPM = new FunctionPassManager(
        PB->buildFunctionSimplificationPipeline(lvl, ThinOrFullLTOPhase::None));
    return llvm::wrap(FPM);
}

API_EXPORT(void)
LLVMPY_DisposePassBuilder(LLVMPassBuilderRef PB) { delete llvm::unwrap(PB); }

} // end extern "C"
