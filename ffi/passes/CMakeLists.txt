cmake_minimum_required(VERSION 3.2)

set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{MACOSX_DEPLOYMENT_TARGET} CACHE STRING "Minimum OS X deployment version")
message( STATUS "MACOSX_DEPLOYMENT_TARGET is ${MACOSX_DEPLOYMENT_TARGET}")

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
