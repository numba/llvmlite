cmake_minimum_required(VERSION 3.2)

find_package(LLVM REQUIRED CONFIG)

add_definitions(${LLVM_DEFINITIONS})

add_definitions(LLVM_DISABLE_ABI_BREAKING_CHECKS_ENFORCING=1)

if (NOT WIN32)
    add_compile_options("-fno-rtti")
endif()

include_directories(${LLVM_INCLUDE_DIRS})

add_subdirectory(hello)
