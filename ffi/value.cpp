#include <string>
#include "llvm-c/Core.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Module.h"
#include "core.h"

extern "C" {

API_EXPORT(void)
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

API_EXPORT(const char *)
LLVMPY_GetValueName(LLVMValueRef Val)
{
    return LLVMGetValueName(Val);
}

API_EXPORT(void)
LLVMPY_SetValueName(LLVMValueRef Val, const char *Name)
{
    LLVMSetValueName(Val, Name);
}

API_EXPORT(LLVMModuleRef)
LLVMPY_GetGlobalParent(LLVMValueRef Val)
{
    return LLVMGetGlobalParent(Val);
}

API_EXPORT(LLVMTypeRef)
LLVMPY_TypeOf(LLVMValueRef Val)
{
    return LLVMTypeOf(Val);
}

API_EXPORT(void)
LLVMPY_SetLinkage(LLVMValueRef Val, int Linkage)
{
    LLVMSetLinkage(Val, (LLVMLinkage)Linkage);
}

API_EXPORT(int)
LLVMPY_GetLinkage(LLVMValueRef Val)
{
    return (int)LLVMGetLinkage(Val);
}

API_EXPORT(void)
LLVMPY_AddFunctionAttr(LLVMValueRef Fn, int Attr)
{
    LLVMAddFunctionAttr(Fn, (LLVMAttribute)Attr);
}

API_EXPORT(int)
LLVMPY_IsDeclaration(LLVMValueRef GV)
{
    return LLVMIsDeclaration(GV);
}

} // end extern "C"
