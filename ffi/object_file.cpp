#include "core.h"

#include "llvm-c/ExecutionEngine.h"
#include "llvm-c/Object.h"

#include "llvm/Object/ObjectFile.h"

#include <stdio.h>

// From lib/Object/Object.cpp
namespace llvm {
inline object::section_iterator *unwrap(LLVMSectionIteratorRef SI) {
    return reinterpret_cast<object::section_iterator *>(SI);
}

inline LLVMSectionIteratorRef wrap(const object::section_iterator *SI) {
    return reinterpret_cast<LLVMSectionIteratorRef>(
        const_cast<object::section_iterator *>(SI));
}
} // namespace llvm

extern "C" {

API_EXPORT(LLVMObjectFileRef)
LLVMPY_CreateObjectFile(const char *buf, const size_t n) {
    return LLVMCreateObjectFile(
        LLVMCreateMemoryBufferWithMemoryRangeCopy(buf, n, ""));
}

API_EXPORT(void)
LLVMPY_DisposeObjectFile(LLVMObjectFileRef O) {
    return LLVMDisposeObjectFile(O);
}

API_EXPORT(LLVMSectionIteratorRef)
LLVMPY_GetSections(LLVMObjectFileRef O) { return LLVMGetSections(O); }

API_EXPORT(void)
LLVMPY_DisposeSectionIterator(LLVMSectionIteratorRef SI) {
    LLVMDisposeSectionIterator(SI);
}

API_EXPORT(void)
LLVMPY_MoveToNextSection(LLVMSectionIteratorRef SI) {
    LLVMMoveToNextSection(SI);
}

API_EXPORT(bool)
LLVMPY_IsSectionIteratorAtEnd(LLVMObjectFileRef O, LLVMSectionIteratorRef SI) {
    return LLVMIsSectionIteratorAtEnd(O, SI);
}

API_EXPORT(const char *)
LLVMPY_GetSectionName(LLVMSectionIteratorRef SI) {
    return LLVMGetSectionName(SI);
}

API_EXPORT(uint64_t)
LLVMPY_GetSectionAddress(LLVMSectionIteratorRef SI) {
    return LLVMGetSectionAddress(SI);
}

API_EXPORT(const char *)
LLVMPY_GetSectionContents(LLVMSectionIteratorRef SI) {
    return LLVMGetSectionContents(SI);
}

API_EXPORT(uint64_t)
LLVMPY_GetSectionSize(LLVMSectionIteratorRef SI) {
    return LLVMGetSectionSize(SI);
}

API_EXPORT(bool)
LLVMPY_IsSectionText(LLVMSectionIteratorRef SI) {
    return (*llvm::unwrap(SI))->isText();
}

} // end extern C
