#include "core.h"

#include "llvm-c/Support.h"

extern "C" {

API_EXPORT(const char *)
LLVMPY_CreateString(const char *msg) { return strdup(msg); }

API_EXPORT(const char *)
LLVMPY_CreateByteString(const char *buf, size_t len) {
    char *dest = (char *)malloc(len + 1);
    if (dest != NULL) {
        memcpy(dest, buf, len);
        dest[len] = '\0';
    }
    return dest;
}

API_EXPORT(void)
LLVMPY_DisposeString(const char *msg) { free(const_cast<char *>(msg)); }

API_EXPORT(LLVMContextRef)
LLVMPY_GetGlobalContext() {
    auto context = LLVMGetGlobalContext();
    return context;
}

API_EXPORT(LLVMContextRef)
LLVMPY_ContextCreate() {
    LLVMContextRef context = LLVMContextCreate();
    return context;
}

API_EXPORT(void)
LLVMPY_ContextDispose(LLVMContextRef context) {
    return LLVMContextDispose(context);
}

API_EXPORT(void)
LLVMPY_SetCommandLine(const char *name, const char *option) {
    const char *argv[] = {name, option};
    LLVMParseCommandLineOptions(2, argv, NULL);
}

} // end extern "C"
