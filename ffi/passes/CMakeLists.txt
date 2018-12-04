cmake_minimum_required(VERSION 3.10)

find_package(LLVM REQUIRED CONFIG)

add_compile_options(-fno-rtti)
add_definitions(${LLVM_DEFINITIONS})


include_directories(${LLVM_INCLUDE_DIRS})

add_subdirectory(hello)
