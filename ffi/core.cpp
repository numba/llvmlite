#include "core.h"
#include "llvm/Support/CommandLine.h"

extern "C" {

API_EXPORT(const char *)
LLVMPY_CreateString(const char *msg) {
    return strdup(msg);
}

API_EXPORT(void)
LLVMPY_DisposeString(const char *msg) {
    free(const_cast<char*>(msg));
}

API_EXPORT(LLVMContextRef)
LLVMPY_GetGlobalContext() {
    return LLVMGetGlobalContext();
}

API_EXPORT(void)
LLVMPY_SetCommandLine(const char *name, const char *option)
{
    const char * argv[] = {name, option};
    llvm::cl::ParseCommandLineOptions(2, argv);
}


} // end extern "C"
