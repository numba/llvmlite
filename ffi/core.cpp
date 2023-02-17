#include "core.h"

#include "llvm-c/Support.h"
#include "llvm/IR/LLVMContext.h"

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
LLVMPY_GetGlobalContext(bool enable_opaque_pointers) {
    LLVMContextRef ctx = LLVMGetGlobalContext();
#if LLVM_VERSION_MAJOR >= 14
    if (enable_opaque_pointers) llvm::unwrap(ctx)->enableOpaquePointers();
#endif
    return ctx;
}

API_EXPORT(LLVMContextRef)
LLVMPY_ContextCreate(bool enable_opaque_pointers) {
    LLVMContextRef ctx = LLVMContextCreate();
#if LLVM_VERSION_MAJOR >= 14
    if (enable_opaque_pointers) llvm::unwrap(ctx)->enableOpaquePointers();
#endif
    return ctx;
}

API_EXPORT(bool)
LLVMPY_SupportsTypedPointers(LLVMContextRef ctx) {
#if LLVM_VERSION_MAJOR >= 13
    return llvm::unwrap(ctx)->supportsTypedPointers();
#else
    return true;
#endif
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
