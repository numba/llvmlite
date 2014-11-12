
cmake_minimum_required(VERSION 2.8.8)

# This will define the name of the solution file in the build directory
project(llvmlite_ffi)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# Set your project compile flags.
# E.g. if using the C++ header files
# you will need to enable C++11 support
# for your compiler.

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

# Define our shared library
add_library(llvmlite SHARED assembly.cpp bitcode.cpp core.cpp initfini.cpp
            module.cpp value.cpp executionengine.cpp transforms.cpp
            passmanagers.cpp targets.cpp dylib.cpp linker.cpp)

# Find the libraries that correspond to the LLVM components
# that we wish to use
# llvm_map_components_to_libnames(llvm_libs support core irreader)
llvm_map_components_to_libnames(llvm_libs all)

# Link against LLVM libraries
target_link_libraries(llvmlite ${llvm_libs})
