#include "core.h"

#include "llvm/IR/Module.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/Support/raw_ostream.h"

#include "llvm-c/Linker.h"

extern "C" {

API_EXPORT(int)
LLVMPY_LinkModules(LLVMModuleRef Dest, LLVMModuleRef Src, const char **Err)
{
    using namespace llvm;
    std::string errorstring;
    llvm::raw_string_ostream errstream(errorstring);

    /* Can't use a closure as that's not compatible with passing a
     * function pointer.  Instead, the required environment is passed
     * as a `void *` context pointer.
     */
    auto diagnose = [] (const DiagnosticInfo &DI, void *c) {
        auto errstream = reinterpret_cast<llvm::raw_string_ostream *>(c);

        switch (DI.getSeverity()) {
        case DS_Error:
        case DS_Warning:
        case DS_Remark:
        case DS_Note:
            // Do something different for each of those?
            break;
        }
        llvm::DiagnosticPrinterRawOStream DP(*errstream);
        DI.print(DP);
    };

    Module *D = unwrap(Dest);
    LLVMContext &Ctx = D->getContext();

    /* Save the current diagnostic handler and set our own */
    LLVMContext::DiagnosticHandlerTy OldDiagnosticHandler =
      Ctx.getDiagnosticHandler();
    void *OldDiagnosticContext = Ctx.getDiagnosticContext();
    Ctx.setDiagnosticHandler((LLVMContext::DiagnosticHandlerTy) diagnose,
                             &errstream, true);

    bool failed = LLVMLinkModules2(Dest, Src);

    /* Restore the original diagnostic handler */
    Ctx.setDiagnosticHandler(OldDiagnosticHandler, OldDiagnosticContext, true);

    if (failed) {
        errstream.flush();
        *Err = LLVMPY_CreateString(errorstring.c_str());
    }

    return failed;
}

} // end extern "C"
