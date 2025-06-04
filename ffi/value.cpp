#include "core.h"
#include "llvm-c/Core.h"
#include <string>

#include <iostream>

// the following is needed for WriteGraph()
#include "llvm/Analysis/CFGPrinter.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/Support/GraphWriter.h"

/* An iterator around a attribute list, including the stop condition */
struct AttributeListIterator {
    typedef llvm::AttributeList::iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    AttributeListIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueAttributeListIterator;
typedef OpaqueAttributeListIterator *LLVMAttributeListIteratorRef;

/* An iterator around a attribute set, including the stop condition */
struct AttributeSetIterator {
    typedef llvm::AttributeSet::iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    AttributeSetIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueAttributeSetIterator;
typedef OpaqueAttributeSetIterator *LLVMAttributeSetIteratorRef;

/* An iterator around a function's blocks, including the stop condition */
struct BlocksIterator {
    typedef llvm::Function::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    BlocksIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueBlocksIterator;
typedef OpaqueBlocksIterator *LLVMBlocksIteratorRef;

/* An iterator around a function's arguments, including the stop condition */
struct ArgumentsIterator {
    typedef llvm::Function::const_arg_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    ArgumentsIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueArgumentsIterator;
typedef OpaqueArgumentsIterator *LLVMArgumentsIteratorRef;

/* An iterator around a basic block's instructions, including the stop condition
 */
struct InstructionsIterator {
    typedef llvm::BasicBlock::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    InstructionsIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueInstructionsIterator;
typedef OpaqueInstructionsIterator *LLVMInstructionsIteratorRef;

/* An iterator around a instruction's operands, including the stop condition */
struct OperandsIterator {
    typedef llvm::Instruction::const_op_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    OperandsIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueOperandsIterator;
typedef OpaqueOperandsIterator *LLVMOperandsIteratorRef;

/* An iterator around a phi node's incoming blocks, including the stop condition
 */
struct IncomingBlocksIterator {
    typedef llvm::PHINode::const_block_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    IncomingBlocksIterator(const_iterator cur, const_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueIncomingBlocksIterator;
typedef OpaqueIncomingBlocksIterator *LLVMIncomingBlocksIteratorRef;

namespace llvm {

static LLVMAttributeListIteratorRef wrap(AttributeListIterator *GI) {
    return reinterpret_cast<LLVMAttributeListIteratorRef>(GI);
}

static AttributeListIterator *unwrap(LLVMAttributeListIteratorRef GI) {
    return reinterpret_cast<AttributeListIterator *>(GI);
}

static LLVMAttributeSetIteratorRef wrap(AttributeSetIterator *GI) {
    return reinterpret_cast<LLVMAttributeSetIteratorRef>(GI);
}

static AttributeSetIterator *unwrap(LLVMAttributeSetIteratorRef GI) {
    return reinterpret_cast<AttributeSetIterator *>(GI);
}

static LLVMBlocksIteratorRef wrap(BlocksIterator *GI) {
    return reinterpret_cast<LLVMBlocksIteratorRef>(GI);
}

static BlocksIterator *unwrap(LLVMBlocksIteratorRef GI) {
    return reinterpret_cast<BlocksIterator *>(GI);
}

static LLVMArgumentsIteratorRef wrap(ArgumentsIterator *GI) {
    return reinterpret_cast<LLVMArgumentsIteratorRef>(GI);
}

static ArgumentsIterator *unwrap(LLVMArgumentsIteratorRef GI) {
    return reinterpret_cast<ArgumentsIterator *>(GI);
}

static LLVMInstructionsIteratorRef wrap(InstructionsIterator *GI) {
    return reinterpret_cast<LLVMInstructionsIteratorRef>(GI);
}

static InstructionsIterator *unwrap(LLVMInstructionsIteratorRef GI) {
    return reinterpret_cast<InstructionsIterator *>(GI);
}

static LLVMOperandsIteratorRef wrap(OperandsIterator *GI) {
    return reinterpret_cast<LLVMOperandsIteratorRef>(GI);
}

static OperandsIterator *unwrap(LLVMOperandsIteratorRef GI) {
    return reinterpret_cast<OperandsIterator *>(GI);
}

static LLVMIncomingBlocksIteratorRef wrap(IncomingBlocksIterator *GI) {
    return reinterpret_cast<LLVMIncomingBlocksIteratorRef>(GI);
}

static IncomingBlocksIterator *unwrap(LLVMIncomingBlocksIteratorRef GI) {
    return reinterpret_cast<IncomingBlocksIterator *>(GI);
}

} // namespace llvm

extern "C" {

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_FunctionAttributesIter(LLVMValueRef F) {
    using namespace llvm;
    Function *func = unwrap<Function>(F);
    AttributeList attrs = func->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(), attrs.end()));
}

API_EXPORT(LLVMAttributeSetIteratorRef)
LLVMPY_ArgumentAttributesIter(LLVMValueRef A) {
    using namespace llvm;
    Argument *arg = unwrap<Argument>(A);
    unsigned argno = arg->getArgNo();
    const AttributeSet attrs =
        arg->getParent()->getAttributes().getParamAttrs(argno);
    return wrap(new AttributeSetIterator(attrs.begin(), attrs.end()));
}

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_CallInstAttributesIter(LLVMValueRef C) {
    using namespace llvm;
    CallInst *inst = unwrap<CallInst>(C);
    AttributeList attrs = inst->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(), attrs.end()));
}

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_InvokeInstAttributesIter(LLVMValueRef C) {
    using namespace llvm;
    InvokeInst *inst = unwrap<InvokeInst>(C);
    AttributeList attrs = inst->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(), attrs.end()));
}

API_EXPORT(LLVMAttributeSetIteratorRef)
LLVMPY_GlobalAttributesIter(LLVMValueRef G) {
    using namespace llvm;
    GlobalVariable *g = unwrap<GlobalVariable>(G);
    AttributeSet attrs = g->getAttributes();
    return wrap(new AttributeSetIterator(attrs.begin(), attrs.end()));
}

API_EXPORT(LLVMBlocksIteratorRef)
LLVMPY_FunctionBlocksIter(LLVMValueRef F) {
    using namespace llvm;
    Function *func = unwrap<Function>(F);
    return wrap(new BlocksIterator(func->begin(), func->end()));
}

API_EXPORT(LLVMArgumentsIteratorRef)
LLVMPY_FunctionArgumentsIter(LLVMValueRef F) {
    using namespace llvm;
    Function *func = unwrap<Function>(F);
    return wrap(new ArgumentsIterator(func->arg_begin(), func->arg_end()));
}

API_EXPORT(LLVMInstructionsIteratorRef)
LLVMPY_BlockInstructionsIter(LLVMValueRef B) {
    using namespace llvm;
    BasicBlock *block = unwrap<BasicBlock>(B);
    return wrap(new InstructionsIterator(block->begin(), block->end()));
}

API_EXPORT(LLVMOperandsIteratorRef)
LLVMPY_InstructionOperandsIter(LLVMValueRef I) {
    using namespace llvm;
    Instruction *inst = unwrap<Instruction>(I);
    return wrap(new OperandsIterator(inst->op_begin(), inst->op_end()));
}

API_EXPORT(LLVMIncomingBlocksIteratorRef)
LLVMPY_PhiIncomingBlocksIter(LLVMValueRef I) {
    using namespace llvm;
    PHINode *inst = unwrap<PHINode>(I);
    return wrap(
        new IncomingBlocksIterator(inst->block_begin(), inst->block_end()));
}

API_EXPORT(const char *)
LLVMPY_AttributeListIterNext(LLVMAttributeListIteratorRef GI) {
    using namespace llvm;
    AttributeListIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return LLVMPY_CreateString((&*iter->cur++)->getAsString().c_str());
    } else {
        return NULL;
    }
}

API_EXPORT(const char *)
LLVMPY_AttributeSetIterNext(LLVMAttributeSetIteratorRef GI) {
    using namespace llvm;
    AttributeSetIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return LLVMPY_CreateString((&*iter->cur++)->getAsString().c_str());
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_BlocksIterNext(LLVMBlocksIteratorRef GI) {
    using namespace llvm;
    BlocksIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(static_cast<const Value *>(&*iter->cur++));
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_ArgumentsIterNext(LLVMArgumentsIteratorRef GI) {
    using namespace llvm;
    ArgumentsIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_InstructionsIterNext(LLVMInstructionsIteratorRef GI) {
    using namespace llvm;
    InstructionsIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_OperandsIterNext(LLVMOperandsIteratorRef GI) {
    using namespace llvm;
    OperandsIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap((&*iter->cur++)->get());
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_IncomingBlocksIterNext(LLVMIncomingBlocksIteratorRef GI) {
    using namespace llvm;
    IncomingBlocksIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(static_cast<const Value *>(*iter->cur++));
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeAttributeListIter(LLVMAttributeListIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeAttributeSetIter(LLVMAttributeSetIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeBlocksIter(LLVMBlocksIteratorRef GI) { delete llvm::unwrap(GI); }

API_EXPORT(void)
LLVMPY_DisposeArgumentsIter(LLVMArgumentsIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeInstructionsIter(LLVMInstructionsIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeOperandsIter(LLVMOperandsIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeIncomingBlocksIter(LLVMIncomingBlocksIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(bool)
LLVMPY_IsConstant(LLVMValueRef Val) { return LLVMIsConstant(Val); }

API_EXPORT(const uint64_t *)
LLVMPY_GetConstantIntRawValue(LLVMValueRef Val, bool *littleEndian) {
    if (littleEndian) {
        *littleEndian = llvm::sys::IsLittleEndianHost;
    }
    if (llvm::ConstantInt *CI =
            llvm::dyn_cast<llvm::ConstantInt>((llvm::Value *)Val)) {
        return CI->getValue().getRawData();
    }
    return nullptr;
}

API_EXPORT(unsigned)
LLVMPY_GetConstantIntNumWords(LLVMValueRef Val) {
    if (llvm::ConstantInt *CI =
            llvm::dyn_cast<llvm::ConstantInt>((llvm::Value *)Val)) {
        return CI->getValue().getNumWords();
    }
    return 0;
}

API_EXPORT(double)
LLVMPY_GetConstantFPValue(LLVMValueRef Val, bool *losesInfo) {
    LLVMBool losesInfo_internal;
    double result = LLVMConstRealGetDouble(Val, &losesInfo_internal);
    if (losesInfo) {
        *losesInfo = losesInfo_internal;
    }
    return result;
}

API_EXPORT(int)
LLVMPY_GetValueKind(LLVMValueRef Val) { return (int)LLVMGetValueKind(Val); }

API_EXPORT(void)
LLVMPY_PrintValueToString(LLVMValueRef Val, const char **outstr) {
    *outstr = LLVMPrintValueToString(Val);
}

API_EXPORT(const char *)
LLVMPY_GetValueName(LLVMValueRef Val) { return LLVMGetValueName(Val); }

API_EXPORT(void)
LLVMPY_SetValueName(LLVMValueRef Val, const char *Name) {
    LLVMSetValueName(Val, Name);
}

API_EXPORT(LLVMModuleRef)
LLVMPY_GetGlobalParent(LLVMValueRef Val) { return LLVMGetGlobalParent(Val); }

API_EXPORT(LLVMTypeRef)
LLVMPY_GlobalGetValueType(LLVMValueRef GlobalVal) {
    return LLVMGlobalGetValueType(GlobalVal);
}

API_EXPORT(void)
LLVMPY_SetLinkage(LLVMValueRef Val, int Linkage) {
    LLVMSetLinkage(Val, (LLVMLinkage)Linkage);
}

API_EXPORT(int)
LLVMPY_GetLinkage(LLVMValueRef Val) { return (int)LLVMGetLinkage(Val); }

API_EXPORT(void)
LLVMPY_SetVisibility(LLVMValueRef Val, int Visibility) {
    LLVMSetVisibility(Val, (LLVMVisibility)Visibility);
}

API_EXPORT(int)
LLVMPY_GetVisibility(LLVMValueRef Val) { return (int)LLVMGetVisibility(Val); }

API_EXPORT(void)
LLVMPY_SetDLLStorageClass(LLVMValueRef Val, int DLLStorageClass) {
    LLVMSetDLLStorageClass(Val, (LLVMDLLStorageClass)DLLStorageClass);
}

API_EXPORT(int)
LLVMPY_GetDLLStorageClass(LLVMValueRef Val) {
    return (int)LLVMGetDLLStorageClass(Val);
}

API_EXPORT(unsigned)
LLVMPY_GetEnumAttributeKindForName(const char *name, size_t len) {
    /* zero is returned if no match */
    return LLVMGetEnumAttributeKindForName(name, len);
}

API_EXPORT(void)
LLVMPY_AddFunctionAttr(LLVMValueRef Fn, unsigned AttrKind) {
    LLVMContextRef ctx = LLVMGetModuleContext(LLVMGetGlobalParent(Fn));
    LLVMAttributeRef attr_ref = LLVMCreateEnumAttribute(ctx, AttrKind, 0);
    LLVMAddAttributeAtIndex(Fn, LLVMAttributeReturnIndex, attr_ref);
}

API_EXPORT(int)
LLVMPY_IsDeclaration(LLVMValueRef GV) { return LLVMIsDeclaration(GV); }

API_EXPORT(void)
LLVMPY_WriteCFG(LLVMValueRef Fval, const char **OutStr, int ShowInst) {
    using namespace llvm;
    Function *F = unwrap<Function>(Fval);
    std::string buffer;
    raw_string_ostream stream(buffer);
    DOTFuncInfo CFGInfo(F, nullptr, nullptr, 0);
    WriteGraph(stream, &CFGInfo, !ShowInst);
    *OutStr = LLVMPY_CreateString(stream.str().c_str());
}

API_EXPORT(const char *)
LLVMPY_GetOpcodeName(LLVMValueRef Val) {
    // try to convert to an instruction value, works for other derived
    // types too
    llvm::Value *unwrapped = llvm::unwrap(Val);
    llvm::Instruction *inst = llvm::dyn_cast<llvm::Instruction>(unwrapped);
    if (inst) {
        return LLVMPY_CreateString(inst->getOpcodeName());
    }
    return LLVMPY_CreateString("");
}

} // end extern "C"
