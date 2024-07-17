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

// FIXME: Remove `enableOpaquePointers' once typed pointers are removed.
API_EXPORT(LLVMContextRef)
LLVMPY_GetGlobalContext(bool enableOpaquePointers) {
    auto context = LLVMGetGlobalContext();
    LLVMContextSetOpaquePointers(context, enableOpaquePointers);
    return context;
}

// FIXME: Remove `enableOpaquePointers' once typed pointers are removed.
API_EXPORT(LLVMContextRef)
LLVMPY_ContextCreate(bool enableOpaquePointers) {
    LLVMContextRef context = LLVMContextCreate();
    LLVMContextSetOpaquePointers(context, enableOpaquePointers);
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
