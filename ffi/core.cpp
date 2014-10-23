#include "core.h"

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
