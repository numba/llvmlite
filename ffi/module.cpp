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


int
LLVMPY_VerifyModule(LLVMModuleRef M, char **OutMsg)
{
    return LLVMVerifyModule(M, LLVMPrintMessageAction, OutMsg);
}


} // end extern "C"


