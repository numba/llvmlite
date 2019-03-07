#include <string>
#include "llvm-c/Core.h"
#include "core.h"

#include <iostream>

// the following is needed for WriteGraph()
#include "llvm/Analysis/CFGPrinter.h"

/* An iterator around a function's blocks, including the stop condition */
struct BlocksIterator {
    typedef llvm::Function::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    BlocksIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueBlocksIterator;
typedef OpaqueBlocksIterator* LLVMBlocksIteratorRef;

/* An iterator around a function's arguments, including the stop condition */
struct ArgumentsIterator {
    typedef llvm::Function::const_arg_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    ArgumentsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueArgumentsIterator;
typedef OpaqueArgumentsIterator* LLVMArgumentsIteratorRef;


/* An iterator around a basic block's instructions, including the stop condition */
struct InstructionsIterator {
    typedef llvm::BasicBlock::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    InstructionsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueInstructionsIterator;
typedef OpaqueInstructionsIterator* LLVMInstructionsIteratorRef;

/* An iterator around a instruction's operands, including the stop condition */
struct OperandsIterator {
    typedef llvm::Instruction::const_op_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    OperandsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueOperandsIterator;
typedef OpaqueOperandsIterator* LLVMOperandsIteratorRef;

namespace llvm {

static LLVMBlocksIteratorRef
wrap(BlocksIterator* GI){
    return reinterpret_cast<LLVMBlocksIteratorRef>(GI);
}

static BlocksIterator*
unwrap(LLVMBlocksIteratorRef GI){
    return reinterpret_cast<BlocksIterator *>(GI);
}

static LLVMArgumentsIteratorRef
wrap(ArgumentsIterator* GI){
    return reinterpret_cast<LLVMArgumentsIteratorRef>(GI);
}

static ArgumentsIterator*
unwrap(LLVMArgumentsIteratorRef GI){
    return reinterpret_cast<ArgumentsIterator *>(GI);
}

static LLVMInstructionsIteratorRef
wrap(InstructionsIterator* GI){
    return reinterpret_cast<LLVMInstructionsIteratorRef>(GI);
}

static InstructionsIterator*
unwrap(LLVMInstructionsIteratorRef GI){
    return reinterpret_cast<InstructionsIterator *>(GI);
}

static LLVMOperandsIteratorRef
wrap(OperandsIterator* GI){
    return reinterpret_cast<LLVMOperandsIteratorRef>(GI);
}

static OperandsIterator*
unwrap(LLVMOperandsIteratorRef GI){
    return reinterpret_cast<OperandsIterator *>(GI);
}


}

extern "C" {

API_EXPORT(LLVMBlocksIteratorRef)
LLVMPY_FunctionBlocksIter(LLVMValueRef F)
{
    using namespace llvm;
    Function* func = unwrap<Function>(F);
    return wrap(new BlocksIterator(func->begin(),
                                   func->end()));
}

API_EXPORT(LLVMArgumentsIteratorRef)
LLVMPY_FunctionArgumentsIter(LLVMValueRef F)
{
    using namespace llvm;
    Function* func = unwrap<Function>(F);
    return wrap(new ArgumentsIterator(func->arg_begin(),
                                      func->arg_end()));
}

API_EXPORT(LLVMInstructionsIteratorRef)
LLVMPY_BlockInstructionsIter(LLVMValueRef B)
{
    using namespace llvm;
    BasicBlock* block = unwrap<BasicBlock>(B);
    return wrap(new InstructionsIterator(block->begin(),
                                         block->end()));
}

API_EXPORT(LLVMOperandsIteratorRef)
LLVMPY_InstructionOperandsIter(LLVMValueRef I)
{
    using namespace llvm;
    Instruction* inst = unwrap<Instruction>(I);
    return wrap(new OperandsIterator(inst->op_begin(),
                                inst->op_end()));
}

API_EXPORT(LLVMValueRef)
LLVMPY_BlocksIterNext(LLVMBlocksIteratorRef GI)
{
    using namespace llvm;
    BlocksIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap(static_cast<const Value*>(&*iter->cur++));
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_ArgumentsIterNext(LLVMArgumentsIteratorRef GI)
{
    using namespace llvm;
    ArgumentsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      //return wrap(static_cast<const Value*>(&*iter->cur++));
      return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_InstructionsIterNext(LLVMInstructionsIteratorRef GI)
{
    using namespace llvm;
    InstructionsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_OperandsIterNext(LLVMOperandsIteratorRef GI)
{
    using namespace llvm;
    OperandsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap((&*iter->cur++)->get());
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeBlocksIter(LLVMBlocksIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeArgumentsIter(LLVMArgumentsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeInstructionsIter(LLVMInstructionsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeOperandsIter(LLVMOperandsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

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

API_EXPORT(const char *)
LLVMPY_PrintType(LLVMTypeRef type)
{
    return LLVMPrintTypeToString(type);
}

API_EXPORT(const char *)
LLVMPY_GetTypeName(LLVMTypeRef type)
{
    // try to convert to a struct type, works for other derived
    // types too
    llvm::Type* unwrapped = llvm::unwrap(type);
    llvm::StructType* ty = llvm::dyn_cast<llvm::StructType>(unwrapped);
    if (ty && !ty->isLiteral()) {
        return strdup(ty->getStructName().str().c_str());
    }
    return strdup("");
}

API_EXPORT(bool)
LLVMPY_TypeIsPointer(LLVMTypeRef type)
{
    return llvm::unwrap(type)->isPointerTy();
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetElementType(LLVMTypeRef type)
{
    llvm::Type* unwrapped = llvm::unwrap(type);
    llvm::PointerType* ty = llvm::dyn_cast<llvm::PointerType>(unwrapped);
    if (ty != nullptr) {
        return llvm::wrap(ty->getElementType());
    }
    return nullptr;
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

API_EXPORT(unsigned)
LLVMPY_GetEnumAttributeKindForName(const char *name, size_t len)
{
    /* zero is returned if no match */
    return LLVMGetEnumAttributeKindForName(name, len);
}

API_EXPORT(void)
LLVMPY_AddFunctionAttr(LLVMValueRef Fn, unsigned AttrKind)
{
    LLVMContextRef ctx = LLVMGetModuleContext(LLVMGetGlobalParent(Fn));
    LLVMAttributeRef attr_ref = LLVMCreateEnumAttribute(ctx, AttrKind, 0);
    LLVMAddAttributeAtIndex(Fn, LLVMAttributeReturnIndex, attr_ref);
}

API_EXPORT(int)
LLVMPY_IsDeclaration(LLVMValueRef GV)
{
    return LLVMIsDeclaration(GV);
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

API_EXPORT(const char *)
LLVMPY_GetOpcodeName(LLVMValueRef Val)
{
    // try to convert to an instruction value, works for other derived
    // types too
    llvm::Value* unwrapped = llvm::unwrap(Val);
    llvm::Instruction* inst = llvm::dyn_cast<llvm::Instruction>(unwrapped);
    if (inst) {
        return strdup(inst->getOpcodeName());
    }
    return strdup("");
}


} // end extern "C"
