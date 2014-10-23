#include <string>
#include "llvm-c/Core.h"
#include "llvm-c/Analysis.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Module.h"
#include "core.h"

extern "C" {

API_EXPORT(void)
LLVMPY_DisposeModule(LLVMModuleRef m) {
    return LLVMDisposeModule(m);
}

API_EXPORT(void)
LLVMPY_PrintModuleToString(LLVMModuleRef M,
                           const char **outstr)
{
    using namespace llvm;
    std::string buf;
    raw_string_ostream os(buf);
    unwrap(M)->print(os, NULL);
    os.flush();
    *outstr = LLVMPY_CreateString(buf.c_str());
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedFunction(LLVMModuleRef M,
                     const char *Name)
{
    return LLVMGetNamedFunction(M, Name);
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedGlobalVariable(LLVMModuleRef M,
                              const char *Name)
{
    using namespace llvm;
    return wrap(unwrap(M)->getGlobalVariable(Name));
}


API_EXPORT(int)
LLVMPY_VerifyModule(LLVMModuleRef M, char **OutMsg)
{
    return LLVMVerifyModule(M, LLVMReturnStatusAction, OutMsg);
}

API_EXPORT(void)
LLVMPY_GetDataLayout(LLVMModuleRef M,
                     const char **DL)
{
    *DL = LLVMGetDataLayout(M);
}


} // end extern "C"
