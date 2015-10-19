#include <string>
#include "llvm-c/Core.h"
#include "core.h"

// the following is needed for WriteGraph()
#include "llvm/Analysis/CFGPrinter.h"

extern "C" {

API_EXPORT(void)
LLVMPY_PrintValueToString(LLVMValueRef Val,
                          const char** outstr)
{
    *outstr = LLVMPrintValueToString(Val);
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
LLVMPY_SetVisibility(LLVMValueRef Val, int Visibility)
{
    LLVMSetVisibility(Val, (LLVMVisibility)Visibility);
}

API_EXPORT(int)
LLVMPY_GetVisibility(LLVMValueRef Val)
{
    return (int)LLVMGetVisibility(Val);
}

API_EXPORT(void)
LLVMPY_SetDLLStorageClass(LLVMValueRef Val, int DLLStorageClass)
{
    LLVMSetDLLStorageClass(Val, (LLVMDLLStorageClass)DLLStorageClass);
}

API_EXPORT(int)
LLVMPY_GetDLLStorageClass(LLVMValueRef Val)
{
    return (int)LLVMGetDLLStorageClass(Val);
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

API_EXPORT(int)
LLVMPY_TypeID(LLVMTypeRef Ty)
{
    using namespace llvm;
    return unwrap<Type>(Ty)->getTypeID();
}

API_EXPORT(void)
LLVMPY_PrintType(LLVMTypeRef Ty, const char **Out) {
    using namespace llvm;
    std::string buf;
    raw_string_ostream out(buf);
    unwrap<Type>(Ty)->print(out);
    *Out = LLVMPY_CreateString(out.str().c_str());
}

API_EXPORT(int)
LLVMPY_IsFunctionType(LLVMTypeRef Ty) {
    using namespace llvm;
    return unwrap<Type>(Ty)->isFunctionTy();
}

API_EXPORT(int)
LLVMPY_IsPointerType(LLVMTypeRef Ty) {
    using namespace llvm;
    return unwrap<Type>(Ty)->isPointerTy();
}

API_EXPORT(int)
LLVMPY_IsLabelType(LLVMTypeRef Ty) {
    using namespace llvm;
    return unwrap<Type>(Ty)->isLabelTy();
}

API_EXPORT(LLVMTypeRef)
LLVMPY_TypePointee(LLVMTypeRef Ty) {
    using namespace llvm;
    return wrap(unwrap<Type>(Ty)->getPointerElementType());
}

API_EXPORT(LLVMBasicBlockRef)
LLVMPY_GetEntryBasicBlock(LLVMValueRef Fn) {
    return LLVMGetEntryBasicBlock(Fn);
}

API_EXPORT(LLVMBasicBlockRef)
LLVMPY_ValueAsBasicBlock(LLVMValueRef Val) {
    return LLVMValueAsBasicBlock(Val);
}

API_EXPORT(LLVMValueRef)
LLVMPY_BasicBlockAsValue(LLVMBasicBlockRef BB) {
    return LLVMBasicBlockAsValue(BB);
}

API_EXPORT(LLVMBasicBlockRef)
LLVMPY_GetNextBasicBlock(LLVMBasicBlockRef BB) {
    return LLVMGetNextBasicBlock(BB);
}

API_EXPORT(LLVMBasicBlockRef)
LLVMPY_GetPreviousBasicBlock(LLVMBasicBlockRef BB) {
    return LLVMGetPreviousBasicBlock(BB);
}


API_EXPORT(void)
LLVMPY_WriteCFG(LLVMValueRef Fval, const char **OutStr, int ShowInst) {
    using namespace llvm;
    Function *F  = unwrap<Function>(Fval);
    std::string buffer;
    raw_string_ostream stream(buffer);
    // Note: The (const Function*)F is necessary to trigger the right behavior.
    //       A non constant Function* will result in the instruction not
    //       printed regardless of the value in the 3rd argument.
    WriteGraph(stream, (const Function*)F, !ShowInst);
    *OutStr = LLVMPY_CreateString(stream.str().c_str());
}


} // end extern "C"
