#include <string>
#include "llvm-c/Core.h"
#include "llvm-c/Analysis.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Module.h"
#include "core.h"

extern "C" {

void
LLVMPY_DisposeModule(LLVMModuleRef m) {
    return LLVMDisposeModule(m);
}

void
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

LLVMValueRef
LLVMPY_GetNamedFunction(LLVMModuleRef M,
                     const char *Name)
{
    return LLVMGetNamedFunction(M, Name);
}

LLVMValueRef
LLVMPY_GetNamedGlobalVariable(LLVMModuleRef M,
                              const char *Name)
{
    using namespace llvm;
    return wrap(unwrap(M)->getGlobalVariable(Name));
}


int
LLVMPY_VerifyModule(LLVMModuleRef M, char **OutMsg)
{
    return LLVMVerifyModule(M, LLVMReturnStatusAction, OutMsg);
}

void
LLVMPY_GetDataLayout(LLVMModuleRef M,
                     const char **DL)
{
    *DL = LLVMGetDataLayout(M);
}




} // end extern "C"


