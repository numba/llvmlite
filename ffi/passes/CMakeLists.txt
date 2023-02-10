cmake_minimum_required(VERSION 3.2)

# TODO(ludger): What is travis, and the outdated xcode doing everywhere?? -> Speak to Graham about this!
if (APPLE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "13.1" CACHE STRING "Minimum OS X deployment version")
    set(MACOSX_DEPLOYMENT_TARGET "13.1")
    set(CMAKE_OSX_SYSROOT "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk")
    LIST(APPEND CMAKE_MODULE_PATH "/opt/homebrew/lib/cmake")
    SET(CMAKE_INSTALL_PREFIX "/Users/lpaehler/miniconda3/envs/llvmlite6")
    SET(LLVM_INSTALL_PREFIX "/Users/lpaehler/miniconda3/envs/llvmlite6")
endif()

project(llvmpy-passes)

#find_package(LLVM REQUIRED CONFIG)

execute_process(
        COMMAND llvm-config --cxxflags ${LLVM_FIND_COMPONENTS}
        RESULT_VARIABLE result_code
        OUTPUT_VARIABLE LLVM_CXXFLAGS
        OUTPUT_STRIP_TRAILING_WHITESPACE
)

set(CMAKE_CXX_FLAGS ${LLVM_CXXFLAGS})

add_definitions(${LLVM_DEFINITIONS})

if (WIN23)
    add_definitions("/D LLVM_DISABLE_ABI_BREAKING_CHECKS_ENFORCING")
else()
    add_definitions("-DLLVM_DISABLE_ABI_BREAKING_CHECKS_ENFORCING")
endif()

if (NOT WIN32)
    add_compile_options("-fno-rtti")
endif()

include_directories(${LLVM_INCLUDE_DIRS})

add_subdirectory(hello)
