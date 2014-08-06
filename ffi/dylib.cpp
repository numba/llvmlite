#include "llvm/Support/DynamicLibrary.h"
#include "llvm/ADT/StringRef.h"

extern "C" {

void*
LLVMPY_SearchAddressOfSymbol(const char *name)
{
    return llvm::sys::DynamicLibrary::SearchForAddressOfSymbol(name);
}


void
LLVMPY_AddSymbol(const char *name,
                 void *addr)
{
    llvm::sys::DynamicLibrary::AddSymbol(name, addr);
}


} // end extern "C"
