#include "core.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/DynamicLibrary.h"

extern "C" {

API_EXPORT(void *)
LLVMPY_SearchAddressOfSymbol(const char *name) {
    return llvm::sys::DynamicLibrary::SearchForAddressOfSymbol(name);
}

API_EXPORT(void)
LLVMPY_AddSymbol(const char *name, void *addr) {
    llvm::sys::DynamicLibrary::AddSymbol(name, addr);
}

API_EXPORT(bool)
LLVMPY_LoadLibraryPermanently(const char *filename, const char **OutError) {
    std::string error;
    bool failed =
        llvm::sys::DynamicLibrary::LoadLibraryPermanently(filename, &error);
    if (failed) {
        *OutError = LLVMPY_CreateString(error.c_str());
    }
    return failed;
}

} // end extern "C"
