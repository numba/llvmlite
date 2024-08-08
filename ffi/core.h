#ifndef LLVMPY_CORE_H_
#define LLVMPY_CORE_H_

#include "llvm-c/Core.h"

// Needed for macros that control version-specific behaviour - included here so
// that they are available in all ffi translation units
#include "llvm/Config/llvm-config.h"

#include <cstdlib>
#include <cstring>

#if defined(_MSC_VER)
#define HAVE_DECLSPEC_DLL
#endif

#if defined(HAVE_DECLSPEC_DLL)
#define API_EXPORT(RTYPE) __declspec(dllexport) RTYPE
#else
#define API_EXPORT(RTYPE) RTYPE
#endif

extern "C" {

API_EXPORT(const char *)
LLVMPY_CreateString(const char *msg);

API_EXPORT(const char *)
LLVMPY_CreateByteString(const char *buf, size_t len);

API_EXPORT(void)
LLVMPY_DisposeString(const char *msg);

// FIXME: Remove `enableOpaquePointers' once typed pointers are removed.
API_EXPORT(LLVMContextRef)
LLVMPY_GetGlobalContext(bool enableOpaquePointers);

// FIXME: Remove `enableOpaquePointers' once typed pointers are removed.
API_EXPORT(LLVMContextRef)
LLVMPY_ContextCreate(bool enableOpaquePointers);

} /* end extern "C" */

#endif /* LLVMPY_CORE_H_ */
