#ifndef LLVMPY_CORE_H_
#define LLVMPY_CORE_H_

#include "llvm-c/Core.h"
#include <cstring>
#include <cstdlib>


#if defined(_MSC_VER)
    #define HAVE_DECLSPEC_DLL
#endif

#if defined(HAVE_DECLSPEC_DLL)
    #define API_EXPORT(RTYPE) __declspec(dllexport) RTYPE
#else
    #define API_EXPORT(RTYPE) RTYPE
#endif

#define LLVM_3_6_OR_ABOVE (LLVM_VERSION_MAJOR > 3 || \
                           (LLVM_VERSION_MAJOR == 3 && LLVM_VERSION_MINOR >= 6))


extern "C" {

API_EXPORT(const char *)
LLVMPY_CreateString(const char *msg);

API_EXPORT(const char *)
LLVMPY_CreateByteString(const char *buf, size_t len);

API_EXPORT(void)
LLVMPY_DisposeString(const char *msg);

API_EXPORT(LLVMContextRef)
LLVMPY_GetGlobalContext();

} /* end extern "C" */


#endif /* LLVMPY_CORE_H_ */
