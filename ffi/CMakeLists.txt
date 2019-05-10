
cmake_minimum_required(VERSION 2.8.8)

# This will define the name of the solution file in the build directory
project(llvmlite_ffi)

include(CheckIncludeFiles)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# Set your project compile flags.
# E.g. if using the C++ header files
# you will need to enable C++11 support
# for your compiler.

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

# Look for SVML
set(CMAKE_REQUIRED_INCLUDES ${LLVM_INCLUDE_DIRS})

CHECK_INCLUDE_FILES("llvm/IR/SVML.inc" HAVE_SVML)
if(HAVE_SVML)
    message(STATUS "SVML found")
    add_definitions(-DHAVE_SVML)
else()
    message(STATUS "SVML not found")
endif()


# Define our shared library
add_library(llvmlite SHARED assembly.cpp bitcode.cpp core.cpp initfini.cpp
            module.cpp value.cpp executionengine.cpp transforms.cpp
            passmanagers.cpp targets.cpp dylib.cpp linker.cpp object_file.cpp)

# Find the libraries that correspond to the LLVM components
# that we wish to use
# llvm_map_components_to_libnames(llvm_libs support core irreader)
llvm_map_components_to_libnames(llvm_libs all)

# Since LLVM 8 "OptRemarks" is built as a shared library only and also appears
# under the llvm_libs for the "all" components map. This breaks static linking
# so the "OptRemarks" library is removed from this list.
list(REMOVE_ITEM llvm_libs "OptRemarks")

# Link against LLVM libraries
target_link_libraries(llvmlite ${llvm_libs})
