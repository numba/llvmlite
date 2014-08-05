#include "core.h"

const char *
LLVMPY_CreateString(const char *msg) {
    return strdup(msg);
}

void
LLVMPY_DisposeString(const char *msg) {
    free(const_cast<char*>(msg));
}

LLVMContextRef
LLVMPY_GetGlobalContext() {
    return LLVMGetGlobalContext();
}
