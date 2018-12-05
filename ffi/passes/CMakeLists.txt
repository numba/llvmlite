cmake_minimum_required(VERSION 3.2)

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
add_subdirectory(refcntopt)
