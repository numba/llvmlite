#include "ffi_types.h"
#include "llvm-c/Target.h"
#include "llvm-c/Transforms/PassBuilder.h"

#include "llvm/IR/Verifier.h"
#include "llvm/Passes/StandardInstrumentations.h"
#include "llvm/Support/CBindingWrapping.h"

/// Helper struct for holding a set of builder options for LLVMRunPasses. This
/// structure is used to keep LLVMRunPasses backwards compatible with future
/// versions in case we modify the options the new Pass Manager utilizes.
class LLVMPassBuilderOptions {
  public:
    explicit LLVMPassBuilderOptions(
        bool DebugLogging = false, bool VerifyEach = false,
        llvm::PipelineTuningOptions PTO = llvm::PipelineTuningOptions())
        : DebugLogging(DebugLogging), VerifyEach(VerifyEach), PTO(PTO) {}

    bool DebugLogging;
    bool VerifyEach;
    llvm::PipelineTuningOptions PTO;
};

static llvm::TargetMachine *unwrap(LLVMTargetMachineRef P) {
    return reinterpret_cast<llvm::TargetMachine *>(P);
}

DEFINE_SIMPLE_CONVERSION_FUNCTIONS(LLVMPassBuilderOptions,
                                   LLVMPassBuilderOptionsRef)

static const LLVMOptimizationLevel mapToLevel(unsigned OptLevel,
                                              unsigned SizeLevel) {
    switch (OptLevel) {
    default:
        llvm_unreachable("Invalid optimization level!");

    case 0:
        return &llvm::OptimizationLevel::O0;

    case 1:
        return &llvm::OptimizationLevel::O1;

    case 2:
        switch (SizeLevel) {
        default:
            llvm_unreachable("Invalid optimization level for size!");

        case 0:
            return &llvm::OptimizationLevel::O2;

        case 1:
            return &llvm::OptimizationLevel::Os;

        case 2:
            return &llvm::OptimizationLevel::Oz;
        }

    case 3:
        return &llvm::OptimizationLevel::O3;
    }
}

extern "C" {

API_EXPORT(LLVMPassBuilder)
LLVMPY_PassManagerBuilderCreate() { return new llvm::PassBuilder(); }

API_EXPORT(LLVMPassBuilderOptionsRef)
LLVMPY_PassManagerBuilderOptionsCreate() {
    return LLVMCreatePassBuilderOptions();
}

API_EXPORT(LLVMModuleAnalysisManager)
LLVMPY_LLVMModuleAnalysisManagerCreate() {
    return new llvm::ModuleAnalysisManager;
}

API_EXPORT(void)
LLVMPY_LLVMModuleAnalysisManagerDispose(LLVMModuleAnalysisManager MAM) {
    delete (MAM);
}

API_EXPORT(LLVMLoopAnalysisManager)
LLVMPY_LLVMLoopAnalysisManagerCreate() { return new llvm::LoopAnalysisManager; }

API_EXPORT(void)
LLVMPY_LLVMLoopAnalysisManagerDispose(LLVMLoopAnalysisManager LAM) {
    delete (LAM);
}

API_EXPORT(LLVMFunctionAnalysisManager)
LLVMPY_LLVMFunctionAnalysisManagerCreate() {
    return new llvm::FunctionAnalysisManager;
}

API_EXPORT(void)
LLVMPY_LLVMFunctionAnalysisManagerDispose(LLVMFunctionAnalysisManager FAM) {
    delete (FAM);
}

API_EXPORT(LLVMCGSCCAnalysisManager)
LLVMPY_LLVMCGSCCAnalysisManagerCreate() {
    return new llvm::CGSCCAnalysisManager;
}

API_EXPORT(void)
LLVMPY_LLVMCGSCCAnalysisManagerDispose(LLVMCGSCCAnalysisManager CGAM) {
    delete (CGAM);
}

API_EXPORT(LLVMPassInstrumentationCallbacks)
LLVMPY_LLVMPassInstrumentationCallbacksCreate() {
    return new llvm::PassInstrumentationCallbacks;
}

API_EXPORT(void)
LLVMPY_LLVMPassInstrumentationCallbacksDispose(
    LLVMPassInstrumentationCallbacks PIC) {
    delete (PIC);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderDispose(LLVMPassBuilder PB,
                                 LLVMPassBuilderOptionsRef Options) {
    // TODO figure out proper deletion
    // delete(PB);
    // LLVMDisposePassBuilderOptions(Options);
}

// Deprecated: no longer exists in LLVM
API_EXPORT(LLVMModulePassManager)
LLVMPY_PassManagerBuilderPopulateModulePassManager(
    LLVMPassBuilder PB, LLVMPassBuilderOptionsRef Options,
    LLVMOptimizationLevel Level, LLVMModulePassManager MPM,
    LLVMModuleAnalysisManager MAM, LLVMLoopAnalysisManager LAM,
    LLVMFunctionAnalysisManager FAM, LLVMCGSCCAnalysisManager CGAM,
    LLVMPassInstrumentationCallbacks PIC) {
    // TODO handle PB memory better
    if (PB)
        delete (PB);

    PB = new llvm::PassBuilder(nullptr, unwrap(Options)->PTO,
                               /*Optional<PGOOptions> PGOOpt =*/{}, PIC);

    // Register all the basic analyses with the managers.
    PB->registerModuleAnalyses(*MAM);
    PB->registerCGSCCAnalyses(*CGAM);
    PB->registerFunctionAnalyses(*FAM);
    PB->registerLoopAnalyses(*LAM);
    PB->crossRegisterProxies(*LAM, *FAM, *CGAM, *MAM);

    MPM = new llvm::ModulePassManager(
        PB->buildPerModuleDefaultPipeline(*Level, false));

    return MPM;
}

API_EXPORT(LLVMOptimizationLevel)
LLVMPY_PassManagerCreateOptimizationLevel(unsigned OptLevel,
                                          unsigned SizeLevel) {
    return mapToLevel(OptLevel, SizeLevel);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetOptLevel(LLVMOptimizationLevel Level) {
    return Level->getSpeedupLevel();
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMOptimizationLevel Level) {
    return Level->getSizeLevel();
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(
    LLVMPassBuilderOptionsRef Options) {
    return unwrap(Options)->PTO.LoopUnrolling;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(
    LLVMPassBuilderOptionsRef Options, LLVMBool Value) {
    LLVMPassBuilderOptionsSetLoopUnrolling(Options, Value);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(
    LLVMPassBuilderOptionsRef Options, unsigned Threshold) {
    LLVMPassBuilderOptionsSetInlinerThreshold(Options, Threshold);
}

API_EXPORT(LLVMFunctionPassManager)
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
    LLVMPassBuilder PB, LLVMPassBuilderOptionsRef Options,
    LLVMOptimizationLevel Level, LLVMFunctionPassManager FPM,
    LLVMModuleAnalysisManager MAM, LLVMLoopAnalysisManager LAM,
    LLVMFunctionAnalysisManager FAM, LLVMCGSCCAnalysisManager CGAM,
    LLVMPassInstrumentationCallbacks PIC) {
    // TODO handle PB memory better
    if (PB)
        delete (PB);

    PB = new llvm::PassBuilder(nullptr, unwrap(Options)->PTO,
                               /*Optional<PGOOptions> PGOOpt =*/{}, PIC);

    // Register all the basic analyses with the managers.
    PB->registerModuleAnalyses(*MAM);
    PB->registerCGSCCAnalyses(*CGAM);
    PB->registerFunctionAnalyses(*FAM);
    PB->registerLoopAnalyses(*LAM);
    PB->crossRegisterProxies(*LAM, *FAM, *CGAM, *MAM);

    // O0 maps to now passes
    if (*Level != llvm::OptimizationLevel::O0)
        FPM->addPass(PB->buildFunctionSimplificationPipeline(
            *Level, llvm::ThinOrFullLTOPhase::None));

    return FPM;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetLoopVectorize(LLVMPassBuilderOptionsRef Options,
                                          int Value) {
    LLVMPassBuilderOptionsSetLoopVectorization(Options, Value);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetLoopVectorize(LLVMPassBuilderOptionsRef Options) {
    return unwrap(Options)->PTO.LoopVectorization;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSLPVectorize(LLVMPassBuilderOptionsRef Options,
                                         int Value) {
    LLVMPassBuilderOptionsSetSLPVectorization(Options, Value);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetSLPVectorize(LLVMPassBuilderOptionsRef Options) {
    return unwrap(Options)->PTO.SLPVectorization;
}

// TODO: Expose additional new options?
// llvm-project/llvm/include/llvm-c/Transforms/PassBuilder.h
/*
void LLVMPassBuilderOptionsSetVerifyEach(LLVMPassBuilderOptionsRef Options,
                                         LLVMBool VerifyEach);

void LLVMPassBuilderOptionsSetDebugLogging(LLVMPassBuilderOptionsRef Options,
                                           LLVMBool DebugLogging);

void LLVMPassBuilderOptionsSetLoopInterleaving(
    LLVMPassBuilderOptionsRef Options, LLVMBool LoopInterleaving);

void LLVMPassBuilderOptionsSetForgetAllSCEVInLoopUnroll(
    LLVMPassBuilderOptionsRef Options, LLVMBool ForgetAllSCEVInLoopUnroll);

void LLVMPassBuilderOptionsSetLicmMssaOptCap(LLVMPassBuilderOptionsRef Options,
                                             unsigned LicmMssaOptCap);

void LLVMPassBuilderOptionsSetLicmMssaNoAccForPromotionCap(
    LLVMPassBuilderOptionsRef Options, unsigned LicmMssaNoAccForPromotionCap);

void LLVMPassBuilderOptionsSetCallGraphProfile(
    LLVMPassBuilderOptionsRef Options, LLVMBool CallGraphProfile);

void LLVMPassBuilderOptionsSetMergeFunctions(LLVMPassBuilderOptionsRef Options,
                                             LLVMBool MergeFunctions);

*/

} // end extern "C"
