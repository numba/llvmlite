
cmake_minimum_required(VERSION 2.8.8)

# This will define the name of the solution file in the build directory
project(llvmlite_ffi)

include(CheckIncludeFiles)

if(NOT MSVC)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fno-rtti -g")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-rtti -g")
endif()

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
            module.cpp value.cpp executionengine.cpp transforms.cpp type.cpp
            passmanagers.cpp targets.cpp dylib.cpp linker.cpp object_file.cpp
            custom_passes.cpp orcjit.cpp memorymanager.cpp)

# Find the libraries that correspond to the LLVM components
# that we wish to use.
# The following line is broken with LLVM 10.0.0 due to a potential bug in
# the LLVM cmake setup, so we use the workaround instead.
# Bug reported upstream at: https://bugs.llvm.org/show_bug.cgi?id=47003
# BROKEN: llvm_map_components_to_libnames(llvm_libs all)
if ($ENV{LLVMLITE_SHARED})
    set(llvm_libs LLVM)
else()
    set(llvm_libs ${LLVM_AVAILABLE_LIBS})
endif()

# Since LLVM 8 "OptRemarks" is built as a shared library only and also appears
# under the llvm_libs for the "all" components map. This breaks static linking
# so the "OptRemarks" library is removed from this list.
list(REMOVE_ITEM llvm_libs "OptRemarks")

# Link against LLVM libraries
target_link_libraries(llvmlite ${llvm_libs})
# -flto and --exclude-libs allow us to remove those parts of LLVM we don't use
if(${CMAKE_SYSTEM_NAME} MATCHES "Linux" OR ${CMAKE_SYSTEM_NAME} MATCHES "FreeBSD")
    set_property(TARGET llvmlite APPEND_STRING PROPERTY LINK_FLAGS "-flto -Wl,--exclude-libs,ALL")
# On Darwin we only include the LLVMPY symbols we require and exclude
# everything else.
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(LLVM_EXPORTED_SYMBOLS "-Wl,-exported_symbol,_LLVMPY_*")
    set_property(TARGET llvmlite APPEND_STRING PROPERTY LINK_FLAGS "${LLVM_EXPORTED_SYMBOLS}")
endif()
