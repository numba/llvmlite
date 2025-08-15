#include "core.h"

extern "C" {

// NOTE: Keep in sync with CMakeLists definitions
#define LLVMLITE_PACKAGE_FORMAT_CONDA 1
#define LLVMLITE_PACKAGE_FORMAT_WHEEL 2

API_EXPORT(int)
LLVMPY_HasSVMLSupport(void) {
#ifdef HAVE_SVML
    return 1;
#else
    return 0;
#endif
}

API_EXPORT(int)
LLVMPY_IsDynamicLLVMLinkageBuild(void) {
#ifdef HAVE_LLVMLITE_SHARED
    return 1;
#else
    return 0;
#endif
}

API_EXPORT(const char *)
LLVMPY_PackageFormat(void) {
#ifndef LLVMLITE_PACKAGE_FORMAT
    return "unspecified";
#elif LLVMLITE_PACKAGE_FORMAT == LLVMLITE_PACKAGE_FORMAT_WHEEL
    return "wheel";
#elif LLVMLITE_PACKAGE_FORMAT == LLVMLITE_PACKAGE_FORMAT_CONDA
    return "conda";
#else
#error "LLVMLITE_PACKAGE_FORMAT must be one of 'wheel' or 'conda'."
#endif
}

API_EXPORT(int)
LLVMPY_IsStaticLibstdcxxLinkageBuild(void) {
#ifdef LLVMLITE_CXX_STATIC_LINK
    return 1;
#else
    return 0;
#endif
}

// NOTE: Keep in sync with CMakeLists definitions
#define LLVMLITE_LLVM_ASSERTIONS_OFF 0
#define LLVMLITE_LLVM_ASSERTIONS_ON 1
#define LLVMLITE_LLVM_ASSERTIONS_UNKNOWN 2

API_EXPORT(const char *)
LLVMPY_LlvmAssertionsState(void) {
#ifndef LLVMLITE_LLVM_ASSERTIONS_STATE
    return "unknown";
#elif LLVMLITE_LLVM_ASSERTIONS_STATE == LLVMLITE_LLVM_ASSERTIONS_OFF
    return "off";
#elif LLVMLITE_LLVM_ASSERTIONS_STATE == LLVMLITE_LLVM_ASSERTIONS_ON
    return "on";
#elif LLVMLITE_LLVM_ASSERTIONS_STATE == LLVMLITE_LLVM_ASSERTIONS_UNKNOWN
    return "unknown";
#else
#error "LLVMLITE_LLVM_ASSERTIONS_STATE is set to an unexpected value"
#endif
}

} // end extern "C"
