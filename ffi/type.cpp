#include "core.h"
#include "llvm-c/Core.h"
#include <string>

#include <iostream>

#include "llvm/IR/Type.h"
#include "llvm/IR/DerivedTypes.h"

struct ElementIterator {
  typedef llvm::ArrayRef<llvm::Type *>::iterator subtype_iterator;
  subtype_iterator cur;
  subtype_iterator end;
  ElementIterator(subtype_iterator cur, subtype_iterator end)
        : cur(cur), end(end) {
        }
};

struct OpaqueElementIterator;
typedef OpaqueElementIterator *LLVMElementIteratorRef;

namespace llvm {
  static LLVMElementIteratorRef wrap(ElementIterator *GI){
    return reinterpret_cast<LLVMElementIteratorRef>(GI);
  }

  static ElementIterator *unwrap(LLVMElementIteratorRef GI){
    return reinterpret_cast<ElementIterator *>(GI);
  }
}

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
        return wrap(static_cast<const Type*>(ty));
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeElementIter(LLVMElementIteratorRef  GI) { delete llvm::unwrap(GI); }

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

API_EXPORT(LLVMTypeRef)
LLVMPY_GetElementType(LLVMTypeRef type) {
    llvm::Type *unwrapped = llvm::unwrap(type);
    llvm::PointerType *ty = llvm::dyn_cast<llvm::PointerType>(unwrapped);
    if (ty != nullptr) {
#if LLVM_VERSION_MAJOR < 14
        return llvm::wrap(ty->getElementType());
#else
        return llvm::wrap(ty->getPointerElementType());
#endif
    }
    return nullptr;
}

}
