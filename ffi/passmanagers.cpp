#include <tuple>

#include "core.h"

#include "llvm/IR/Module.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/ADT/SmallString.h"

#include "llvm-c/Transforms/Scalar.h"
#include "llvm-c/Transforms/IPO.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/IPO.h"
#include "llvm/PassRegistry.h"
#include "llvm/PassSupport.h"

using namespace llvm;

/*
 * Exposed API
 */

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

API_EXPORT(bool)
LLVMPY_AddPassByArg(LLVMPassManagerRef PM, const char* passArg) {
    auto passManager = llvm::unwrap(PM);
    auto registry = PassRegistry::getPassRegistry();
    const auto* passInfo = registry->getPassInfo(llvm::StringRef(passArg));
    if (passInfo == nullptr) {
        return false;
    }
    auto pass = passInfo->createPass();
    passManager->add(pass);
    return true;
}

namespace {
    class NameSavingPassRegListener : public llvm::PassRegistrationListener {
    public:
    NameSavingPassRegListener() : stream_buf_(), sstream_(stream_buf_) { }
    void passEnumerate(const llvm::PassInfo* passInfo) override {
        if (stream_buf_.size() != 0) {
            sstream_ << ",";

        }
        sstream_ << passInfo->getPassArgument() << ":" << passInfo->getPassName();
    }

    const char* getNames() {
        return stream_buf_.c_str();
    }

    private:
    llvm::SmallString<128> stream_buf_;
    llvm::raw_svector_ostream sstream_;
    };
}

API_EXPORT(LLVMPassRegistryRef)
LLVMPY_GetPassRegistry() {
    return LLVMGetGlobalPassRegistry();
}

API_EXPORT(void)
LLVMPY_ListRegisteredPasses(LLVMPassRegistryRef PR, const char** out) {
    auto registry = unwrap(PR);
    auto listener = llvm::make_unique<NameSavingPassRegListener>();
    registry->enumerateWith(listener.get());
    *out = LLVMPY_CreateString(listener->getNames());
}

} // end extern "C"
