//    void 	LLVMPassManagerBuilderPopulateLTOPassManager (LLVMPassManagerBuilderRef PMB, LLVMPassManagerRef PM, LLVMBool Internalize, LLVMBool RunInliner)


#include "core.h"
#include "llvm/IR/Module.h"
#include "llvm/Linker/Linker.h"

extern "C" {

int
LLVMPY_LinkModules(LLVMModuleRef Dest, LLVMModuleRef Src, unsigned Mode,
                   const char **Err)
{
    using namespace llvm;
    std::string errorstring;
    bool failed = Linker::LinkModules(unwrap(Dest), unwrap(Src), Mode,
                                      &errorstring);
    if (failed) {
        *Err = LLVMPY_CreateString(errorstring.c_str());
    }
    return failed;
}

} // end extern "C"
