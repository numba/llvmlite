#include <tuple>

#include "core.h"

#include "llvm/IR/Module.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm-c/Transforms/IPO.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/IPO.h"
#include "llvm/Support/ToolOutputFile.h"
#include "llvm/Support/YAMLTraits.h"
#include "llvm/Support/FileSystem.h"

using namespace llvm;


/* Helpers to override the diagnostic handler when running
 * optimizations.
 * The default diagnostic handler prints some remarks unconditionally,
 * see http://lists.llvm.org/pipermail/llvm-dev/2016-July/102252.html
 */
typedef std::tuple<LLVMContext::DiagnosticHandlerTy, void *> diag_handler_t;



/*
A single RAII object to keep track of the optimization remark file.
*/
struct OptRemarkContext {
    LLVMContext &Ctx;
    std::unique_ptr<llvm::tool_output_file> OptRecordFile;

    OptRemarkContext(LLVMContext &Ctx, const std::string &record_filename="")
    : Ctx(Ctx) {

        if (record_filename.size()) {
            // Make OptRecordFile to contain the optimization remark
            std::error_code EC;

            auto Flags = sys::fs::F_None;

            OptRecordFile =
                llvm::make_unique<llvm::tool_output_file>(record_filename,
                                                          EC, Flags);
            if (EC) {
                // Failed to open file
                raw_ostream &out = errs();
                DiagnosticPrinterRawOStream DP(out);
                out << "llvmlite failed to open optimization remark file "
                    << record_filename
                    << ". Error: "
                    << EC.message()
                    << "\n";
            } else {
                // This will enable optimization remarks
                Ctx.setDiagnosticsOutputFile(
                    llvm::make_unique<yaml::Output>(OptRecordFile->os()));
            }
        }
    }

    ~OptRemarkContext() {
        if (OptRecordFile) {
            // Don't delete the remark file
            OptRecordFile->keep();
            // Reset remark file
            Ctx.setDiagnosticsOutputFile(nullptr);
        }
    }
};

static diag_handler_t
SetOptimizationDiagnosticHandler(LLVMContext &Ctx)
{
    auto diagnose = [] (const DiagnosticInfo &DI, void *c) {
        // If an error, print the message and bail out (as the default
        // handler does).
        DiagnosticSeverity DS = DI.getSeverity();
        if (DS == DS_Error) {
            raw_ostream &out = errs();
            DiagnosticPrinterRawOStream DP(out);
            out << "LLVM error: ";
            DI.print(DP);
            out << "\n";
            exit(1);
        }
    };
    /* Save the current diagnostic handler and set our own */
    diag_handler_t OldHandler(Ctx.getDiagnosticHandler(),
                              Ctx.getDiagnosticContext());
    Ctx.setDiagnosticHandler((LLVMContext::DiagnosticHandlerTy) diagnose,
                             nullptr);
    return OldHandler;
}

static void
UnsetOptimizationDiagnosticHandler(LLVMContext &Ctx, diag_handler_t OldHandler)
{
    Ctx.setDiagnosticHandler(std::get<0>(OldHandler), std::get<1>(OldHandler));

}


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
LLVMPY_RunPassManagerWithRemarks(LLVMPassManagerRef PM,
                                 LLVMModuleRef M,
                                 const char *record_filename)
{
    /* Save the current diagnostic handler and set our own */
    LLVMContext &Ctx = unwrap(M)->getContext();
    auto OldHandler = SetOptimizationDiagnosticHandler(Ctx);
    OptRemarkContext remarkcontext(Ctx, record_filename);

    int r = LLVMRunPassManager(PM, M);

    UnsetOptimizationDiagnosticHandler(Ctx, OldHandler);
    return r;
}

API_EXPORT(int)
LLVMPY_RunPassManager(LLVMPassManagerRef PM,
                      LLVMModuleRef M)
{
    return LLVMPY_RunPassManagerWithRemarks(PM, M, "");
}


API_EXPORT(int)
LLVMPY_RunFunctionPassManagerWithRemarks(LLVMPassManagerRef PM,
                                         LLVMValueRef F,
                                         const char *record_filename)
{
    /* Save the current diagnostic handler and set our own */
    LLVMContext &Ctx = unwrap(F)->getContext();
    auto OldHandler = SetOptimizationDiagnosticHandler(Ctx);
    OptRemarkContext remarkcontext(Ctx, record_filename);

    int r = LLVMRunFunctionPassManager(PM, F);

    UnsetOptimizationDiagnosticHandler(Ctx, OldHandler);
    return r;
}


API_EXPORT(int)
LLVMPY_RunFunctionPassManager(LLVMPassManagerRef PM,
                              LLVMValueRef F)
{
    return LLVMPY_RunFunctionPassManagerWithRemarks(PM, F, "");
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
