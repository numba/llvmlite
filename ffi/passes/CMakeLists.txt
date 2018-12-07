cmake_minimum_required(VERSION 3.2)

if (APPLE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.9" CACHE STRING "Minimum OS X deployment version")
    set(MACOSX_DEPLOYMENT_TARGET "10.9")
    set(CMAKE_OSX_SYSROOT "/Applications/Xcode-9.4.1.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk")
    set(CMAKE_INSTALL_PREFIX "$ENV{HOME}/miniconda3/envs/travisci")
    message( STATUS "prefix is ${CMAKE_INSTALL_PREFIX}")
    message( STATUS "MACOSX sysroot is ${CMAKE_OSX_SYSROOT}")
    list(INSERT CMAKE_MODULE_PATH "$ENV{HOME}/miniconda3/envs/travisci/lib/cmake/" 0)
    message( STATUS "cmake_modules are ${CMAKE_MODULE_PATH}" )
endif()

project(llvmpy-passes)

find_package(LLVM REQUIRED CONFIG)

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
