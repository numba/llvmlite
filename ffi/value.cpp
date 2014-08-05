#include <string>
#include "llvm-c/Core.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Module.h"
#include "core.h"

extern "C" {

void
LLVMPY_PrintValueToString(LLVMValueRef Val,
                          const char** outstr)
{
    using namespace llvm;

    std::string buf;
    raw_string_ostream os(buf);

    if (unwrap(Val))
        unwrap(Val)->print(os);
    else
        os << "Printing <null> Value";

    os.flush();
    *outstr = LLVMPY_CreateString(buf.c_str());
}


void
LLVMPY_GetValueName(LLVMValueRef Val, const char** outstr)
{
    *outstr = LLVMGetValueName(Val);
}


} // end extern "C"


