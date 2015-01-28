#include "core.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/Linker/Linker.h"
#include "llvm/Support/raw_ostream.h"

extern "C" {

API_EXPORT(int)
LLVMPY_LinkModules(LLVMModuleRef Dest, LLVMModuleRef Src, unsigned Mode,
                   const char **Err)
{
    using namespace llvm;
    std::string errorstring;
#if LLVM_3_6_OR_ABOVE
    llvm::raw_string_ostream errstream(errorstring);
    auto diagnose = [&] (const DiagnosticInfo &DI) {
        switch (DI.getSeverity()) {
        case DS_Error:
        case DS_Warning:
        case DS_Remark:
        case DS_Note:
            // Do something different for each of those?
            break;
        }
        llvm::DiagnosticPrinterRawOStream DP(errstream);
        DI.print(DP);
    };
    bool failed = Linker::LinkModules(unwrap(Dest), unwrap(Src), diagnose);
    if (failed) {
        errstream.flush();
        *Err = LLVMPY_CreateString(errorstring.c_str());
    }
#else
    bool failed = Linker::LinkModules(unwrap(Dest), unwrap(Src), Mode,
                                      &errorstring);
    if (failed) {
        *Err = LLVMPY_CreateString(errorstring.c_str());
    }
#endif
    return failed;
}

} // end extern "C"
