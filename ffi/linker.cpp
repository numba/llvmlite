#include "core.h"

#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/raw_ostream.h"

#include "llvm-c/Linker.h"

extern "C" {

API_EXPORT(int)
LLVMPY_LinkModules(LLVMModuleRef Dest, LLVMModuleRef Src, const char **Err) {
    using namespace llvm;
    std::string errorstring;
    llvm::raw_string_ostream errstream(errorstring);
    Module *D = unwrap(Dest);
    LLVMContext &Ctx = D->getContext();

    // This exists at the change to LLVM 6.x
    // Link error diagnostics end up with a call to abort()
    // install this handler to instead extract the reason for failure
    // and report it.
    class ReportNotAbortDiagnosticHandler : public DiagnosticHandler {
      public:
        ReportNotAbortDiagnosticHandler(llvm::raw_string_ostream &s)
            : raw_stream(s) {}

        bool handleDiagnostics(const DiagnosticInfo &DI) override {
            llvm::DiagnosticPrinterRawOStream DP(raw_stream);
            DI.print(DP);
            return true;
        }

      private:
        llvm::raw_string_ostream &raw_stream;
    };

    // save current handler as "old"
    auto OldDiagnosticHandler = Ctx.getDiagnosticHandler();

    Ctx.setDiagnosticHandler(
        std::make_unique<ReportNotAbortDiagnosticHandler>(errstream));

    // link
    bool failed = LLVMLinkModules2(Dest, Src);

    // put old handler back
    Ctx.setDiagnosticHandler(std::move(OldDiagnosticHandler));

    // if linking failed extract the reason for the failure
    if (failed) {
        errstream.flush();
        *Err = LLVMPY_CreateString(errorstring.c_str());
    }

    return failed;
}

} // end extern "C"
