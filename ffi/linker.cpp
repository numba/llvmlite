#include "core.h"
#include "llvm-c/Linker.h"

extern "C" {

API_EXPORT(int)
LLVMPY_LinkModules(LLVMModuleRef Dest, LLVMModuleRef Src)
{
    return LLVMLinkModules2(Dest, Src);
}

} // end extern "C"
