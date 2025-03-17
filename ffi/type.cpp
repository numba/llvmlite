#include "core.h"
#include "llvm-c/Core.h"
#include <string>

#include <iostream>

#include "llvm/IR/DerivedTypes.h"
#include "llvm/IR/Type.h"

struct ElementIterator {
    typedef llvm::ArrayRef<llvm::Type *>::iterator subtype_iterator;
    subtype_iterator cur;
    subtype_iterator end;
    ElementIterator(subtype_iterator cur, subtype_iterator end)
        : cur(cur), end(end) {}
};

struct OpaqueElementIterator;
typedef OpaqueElementIterator *LLVMElementIteratorRef;

namespace llvm {
static LLVMElementIteratorRef wrap(ElementIterator *GI) {
    return reinterpret_cast<LLVMElementIteratorRef>(GI);
}

static ElementIterator *unwrap(LLVMElementIteratorRef GI) {
    return reinterpret_cast<ElementIterator *>(GI);
}
} // namespace llvm

extern "C" {

API_EXPORT(LLVMElementIteratorRef)
LLVMPY_ElementIter(LLVMTypeRef Val) {
    using namespace llvm;
    llvm::Type *ty = llvm::unwrap(Val);
    auto elements = ty->subtypes();
    return wrap(new ElementIterator(elements.begin(), elements.end()));
}

API_EXPORT(LLVMTypeRef)
LLVMPY_ElementIterNext(LLVMElementIteratorRef GI) {
    using namespace llvm;
    ElementIterator *iter = unwrap(GI);
    if (iter->cur != iter->end) {
        const Type *ty = *(iter->cur);
        iter->cur++;
        return wrap(static_cast<const Type *>(ty));
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeElementIter(LLVMElementIteratorRef GI) {
    delete llvm::unwrap(GI);
}

API_EXPORT(int)
LLVMPY_GetTypeKind(LLVMTypeRef Val) { return (int)LLVMGetTypeKind(Val); }

API_EXPORT(LLVMTypeRef)
LLVMPY_TypeOf(LLVMValueRef Val) { return LLVMTypeOf(Val); }

API_EXPORT(const char *)
LLVMPY_PrintType(LLVMTypeRef type) {
    char *str = LLVMPrintTypeToString(type);
    const char *out = LLVMPY_CreateString(str);
    LLVMDisposeMessage(str);
    return out;
}

API_EXPORT(const char *)
LLVMPY_GetTypeName(LLVMTypeRef type) {
    // try to convert to a struct type, works for other derived
    // types too
    llvm::Type *unwrapped = llvm::unwrap(type);
    llvm::StructType *ty = llvm::dyn_cast<llvm::StructType>(unwrapped);
    if (ty && !ty->isLiteral()) {
        return LLVMPY_CreateString(ty->getStructName().str().c_str());
    }
    return LLVMPY_CreateString("");
}

API_EXPORT(bool)
LLVMPY_TypeIsPointer(LLVMTypeRef type) {
    return llvm::unwrap(type)->isPointerTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsArray(LLVMTypeRef type) { return llvm::unwrap(type)->isArrayTy(); }

API_EXPORT(bool)
LLVMPY_TypeIsVector(LLVMTypeRef type) {
    return llvm::unwrap(type)->isVectorTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsStruct(LLVMTypeRef type) {
    return llvm::unwrap(type)->isStructTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsFunction(LLVMTypeRef type) {
    return llvm::unwrap(type)->isFunctionTy();
}

API_EXPORT(bool)
LLVMPY_IsFunctionVararg(LLVMTypeRef type) {
    llvm::Type *unwrapped = llvm::unwrap(type);
    llvm::FunctionType *ty = llvm::dyn_cast<llvm::FunctionType>(unwrapped);
    if (ty != nullptr) {
        return ty->isVarArg();
    }
    return false;
}

API_EXPORT(int)
LLVMPY_GetTypeElementCount(LLVMTypeRef type) {
    llvm::Type *unwrapped = llvm::unwrap(type);
    if (unwrapped->isArrayTy()) {
        return unwrapped->getArrayNumElements();
    }
    if (unwrapped->isVectorTy()) {
        // Fixed vector: get exact number of elements
        llvm::FixedVectorType *fixedvec =
            llvm::dyn_cast<llvm::FixedVectorType>(unwrapped);
        if (fixedvec != nullptr) {
            return fixedvec->getNumElements();
        }

        // Scalable vector: get minimum elements
        llvm::ScalableVectorType *scalablevec =
            llvm::dyn_cast<llvm::ScalableVectorType>(unwrapped);
        if (scalablevec != nullptr) {
            return scalablevec->getMinNumElements();
        }
    }
    // Not an array nor vector
    return -1;
}

API_EXPORT(uint64_t)
LLVMPY_GetTypeBitWidth(LLVMTypeRef type) {
    llvm::Type *unwrapped = llvm::unwrap(type);
    auto size = unwrapped->getPrimitiveSizeInBits();
    return size.getFixedValue();
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetReturnType(LLVMTypeRef type) { return LLVMGetReturnType(type); }

API_EXPORT(unsigned)
LLVMPY_CountParamTypes(LLVMTypeRef type) { return LLVMCountParamTypes(type); }

API_EXPORT(void)
LLVMPY_GetParamTypes(LLVMTypeRef type, LLVMTypeRef *out_types) {
    LLVMGetParamTypes(type, out_types);
}

API_EXPORT(bool)
LLVMPY_IsPackedStruct(LLVMTypeRef type) { return LLVMIsPackedStruct(type); }

API_EXPORT(bool)
LLVMPY_IsOpaqueStruct(LLVMTypeRef type) { return LLVMIsOpaqueStruct(type); }

API_EXPORT(bool)
LLVMPY_IsLiteralStruct(LLVMTypeRef type) { return LLVMIsLiteralStruct(type); }

} // end extern "C"
