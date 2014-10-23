#include "core.h"
#include "llvm/Support/DynamicLibrary.h"
#include "llvm/ADT/StringRef.h"

extern "C" {

API_EXPORT(void *)
LLVMPY_SearchAddressOfSymbol(const char *name)
{
    return llvm::sys::DynamicLibrary::SearchForAddressOfSymbol(name);
}


API_EXPORT(void)
LLVMPY_AddSymbol(const char *name,
                 void *addr)
{
    llvm::sys::DynamicLibrary::AddSymbol(name, addr);
}


} // end extern "C"
