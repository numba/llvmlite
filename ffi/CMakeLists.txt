cmake_minimum_required(VERSION 3.13)

# This will define the name of the solution file in the build directory
project(llvmlite_ffi)

include(CheckIncludeFiles)
include(CheckLibraryExists)
include(CheckCXXCompilerFlag)
# Work around llvm/llvm-project#83802 - LLVM's Findzstd.cmake uses variables
# that require including `GNUInstallDirs`, but it does not include it itself.
include(GNUInstallDirs)

set(CMAKE_CXX_STANDARD 17)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# NOTE: Keep this in sync with the version that llvmlite is declared to support
set(LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT 15)

# Check LLVM version is supported or intentionally overridden.
if (NOT DEFINED LLVM_VERSION_MAJOR)
    message(FATAL_ERROR "LLVM CMake export does not define LLVM_VERSION_MAJOR")
else()
    if (LLVMLITE_SKIP_LLVM_VERSION_CHECK)
        if (LLVM_VERSION_MAJOR EQUAL LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT)
            message(WARNING
            "LLVMLITE_SKIP_LLVM_VERSION_CHECK is set but the current version \
            ${LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT} is supported!")
        else()
            message(WARNING
            "LLVMLITE_SKIP_LLVM_VERSION_CHECK is set, build is against an \
            unsupported version of LLVM (${LLVM_VERSION_MAJOR}). Supported \
            version is ${LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT}.")
        endif()
    else()
        if (NOT LLVM_VERSION_MAJOR EQUAL LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT)
            message(FATAL_ERROR
            "LLVM CMake export states LLVM version is ${LLVM_VERSION_MAJOR}, \
            llvmlite only officially supports \
            ${LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT}.")
        endif()
    endif()
endif()

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

# Check for presence of the SVML patch in the LLVM build
set(CMAKE_REQUIRED_INCLUDES ${LLVM_INCLUDE_DIRS})

CHECK_INCLUDE_FILES("llvm/IR/SVML.inc" HAVE_SVML)
if(HAVE_SVML)
    message(STATUS "SVML found")
    add_definitions(-DHAVE_SVML)
else()
    message(STATUS "SVML not found")
endif()


# Capture the package format
# LLVMLITE_PACKAGE_FORMAT the target package format, if set must be one of
# 'wheel' or 'conda', this is used by the llvmlite maintainers in testing.

# Keep in sync with config.cpp defines
set(LLVMLITE_PACKAGE_FORMAT_CONDA "1")
set(LLVMLITE_PACKAGE_FORMAT_WHEEL "2")

string(TOLOWER "${LLVMLITE_PACKAGE_FORMAT}" lowercase_LLVMLITE_PACKAGE_FORMAT)
if(lowercase_LLVMLITE_PACKAGE_FORMAT STREQUAL "conda" OR
   lowercase_LLVMLITE_PACKAGE_FORMAT STREQUAL "wheel")
    message(STATUS
    "LLVMLITE_PACKAGE_FORMAT option is set, capturing this is a \
'${lowercase_LLVMLITE_PACKAGE_FORMAT}' format build")
    if(lowercase_LLVMLITE_PACKAGE_FORMAT STREQUAL "conda")
        add_definitions(
        -DLLVMLITE_PACKAGE_FORMAT=${LLVMLITE_PACKAGE_FORMAT_CONDA})
    else()
        add_definitions(
        -DLLVMLITE_PACKAGE_FORMAT=${LLVMLITE_PACKAGE_FORMAT_WHEEL})
    endif()
    message(STATUS
    "LLVMLITE_PACKAGE_FORMAT is ${lowercase_LLVMLITE_PACKAGE_FORMAT}")
elseif("${lowercase_LLVMLITE_PACKAGE_FORMAT}" STREQUAL "")
    # present but not set
else()
    message(FATAL_ERROR "Invalid value for package format: \
'${LLVMLITE_PACKAGE_FORMAT}', expect one of 'conda' or 'wheel'.")
endif()

# Inherited from Makefile system, not tested on unsupported targets (BSD).
if(UNIX AND NOT APPLE)
    set(LLVMLITE_FLTO_DEFAULT ON)
    option(LLVMLITE_FLTO
           "Enable LTO"
           ${LLVMLITE_FLTO_DEFAULT})
    if (LLVMLITE_FLTO)
        check_cxx_compiler_flag(-flto HAVE_FLTO)
        if(NOT HAVE_FLTO)
            message(FATAL_ERROR "-flto flag is not supported by the compiler")
        endif()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -flto")
    endif()
endif()

# Define the shared library
add_library(llvmlite SHARED assembly.cpp bitcode.cpp core.cpp initfini.cpp
            module.cpp value.cpp executionengine.cpp transforms.cpp type.cpp
            passmanagers.cpp targets.cpp dylib.cpp linker.cpp object_file.cpp
            custom_passes.cpp orcjit.cpp memorymanager.cpp newpassmanagers.cpp
            config.cpp)


# Determine whether libstdc++ should be statically linked (or not).
# GNU g++ and presumably clang on non-apple systems can probably deal with this.
if(UNIX AND NOT APPLE)
    set(LLVMLITE_CXX_STATIC_LINK_DEFAULT OFF)
    option(LLVMLITE_CXX_STATIC_LINK
           "Enable C++ static linking in llvmlite (GNU Compilers)"
           ${LLVMLITE_CXX_STATIC_LINK_DEFAULT})

    # See if static libc++ is requested
    if (LLVMLITE_CXX_STATIC_LINK)
        check_cxx_compiler_flag(-static-libstdc++ HAVE_STATIC_LIBSTDCXX)
        if(NOT HAVE_STATIC_LIBSTDCXX)
            message(FATAL_ERROR "LLVMLITE_CXX_STATIC_LINK was requested but
                    the compiler does not support the flag")
        endif()
        add_definitions(-DLLVMLITE_CXX_STATIC_LINK=1)
        target_link_options(llvmlite PRIVATE -static-libstdc++)
    endif()
endif()


# RTTI handling: This is a little awkward, it's a 3-state variable so cannot be
# an option. The states are user defined as ON or OFF, or user has not set so
# inherit from LLVM.
if(UNIX AND NOT APPLE)
    string(TOLOWER "${LLVMLITE_USE_RTTI}" lowercase_LLVMLITE_USE_RTTI)
    if(lowercase_LLVMLITE_USE_RTTI STREQUAL "on")
        message(STATUS
            "LLVMLITE_USE_RTTI override is set, RTTI is ON.")
        set(LLVMLITE_USE_RTTI_FLAG ON)
    elseif(lowercase_LLVMLITE_USE_RTTI STREQUAL "off")
        message(STATUS
            "LLVMLITE_USE_RTTI override is set, RTTI is OFF.")
        set(LLVMLITE_USE_RTTI_FLAG OFF)
    elseif(lowercase_LLVMLITE_USE_RTTI STREQUAL "")
        if(DEFINED LLVM_ENABLE_RTTI)
            message(STATUS
            "LLVMLITE_USE_RTTI not set, inheriting RTTI flags from LLVM as: \
${LLVM_ENABLE_RTTI}.")
            set(LLVMLITE_USE_RTTI_FLAG ${LLVM_ENABLE_RTTI})
        else()
            message(FATAL_ERROR "Both LLVMLITE_USE_RTTI and LLVM_ENABLE_RTTI \
                                 are not set, cannot inherit RTTI setting from \
                                 LLVM, user must override by setting \
                                 LLVMLITE_USE_RTTI")
        endif()
    else()
        message(FATAL_ERROR "LLVMLITE_USE_RTTI is set to an unknown value:
        ${LLVMLITE_USE_RTTI}.")
    endif()

    # unconditionally strip out -fno-rtti, it will be added to the target
    # if needed
    set(FLAG_NO_RTTI "-fno-rtti")
    set(OLD_CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS})
    string(REPLACE "${FLAG_NO_RTTI} " "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    if(LLVMLITE_USE_RTTI_FLAG)
        if(NOT ${OLD_CMAKE_CXX_FLAGS} STREQUAL ${CMAKE_CXX_FLAGS})
            message(STATUS "-fno-rtti was removed from CXXFLAGS.")
        else()
            message(STATUS "-fno-rtti is not in CXXFLAGS, nothing to do.")
        endif()
    else()
        # check for the flag and add it unconditionally (adding it more than
        # once is "ok").
        check_cxx_compiler_flag(${FLAG_NO_RTTI} HAVE_FNO_RTTI)
        if (NOT HAVE_FNO_RTTI)
            message(FATAL_ERROR
            "Compiler must support ${FLAG_NO_RTTI} option if it is requested")
        endif()
        target_compile_options(llvmlite PRIVATE ${FLAG_NO_RTTI})
    endif()
endif()


# Check if the LLVMLITE_SHARED build flag is set. Default is static. This option
# is baked into the binary for testing purposes.
# Find the libraries that correspond to the LLVM components needed based on the
# build flag.
set(LLVMLITE_SHARED_DEFAULT OFF)
option(LLVMLITE_SHARED
       "Enable dynamic linkage against LLVM, default is OFF (i.e. static link)"
       ${LLVMLITE_SHARED_DEFAULT})


if (LLVMLITE_SHARED)
    check_library_exists(LLVM LLVMGetVersion "" HAVE_LIBRARY_LLVM)
    if(NOT HAVE_LIBRARY_LLVM)
        message(FATAL_ERROR "Could not find libLLVM")
    endif()
    set(llvm_libs LLVM)
    message(STATUS
    "LLVMLITE_SHARED is ON, using dynamic linkage against LLVM")
    add_definitions(-DHAVE_LLVMLITE_SHARED)
else()
    # This doesn't work:
    # llvm_map_components_to_libnames(llvm_libs all)
    # xref: https://bugs.llvm.org/show_bug.cgi?id=47003
    # This is a workaround based on knowing what is needed. Do not set llvm_libs
    # to the cached LLVM_AVAILABLE_LIBS, it may contain the dynamic `LLVM`
    # library, see llvmlite#1234 (yes, it's #1234, not a placeholder).
    set(LLVM_COMPONENTS mcjit
                        orcjit
                        AsmPrinter
                        AllTargetsCodeGens
                        AllTargetsAsmParsers
                        IntelJITEvents)
    llvm_map_components_to_libnames(llvm_libs ${LLVM_COMPONENTS})
    message(STATUS
    "LLVMLITE_SHARED is OFF, using static linkage against LLVM")
endif()

# If this is a static link to LLVM, bake in whether LLVM has assertions enabled.
# 3 states, on, off, and unknown
# Keep in sync with config.cpp defines
set(LLVMLITE_LLVM_ASSERTIONS_OFF "0")
set(LLVMLITE_LLVM_ASSERTIONS_ON "1")
set(LLVMLITE_LLVM_ASSERTIONS_UNKNOWN "2")

if(LLVMLITE_SHARED)
    add_definitions(
    -DLLVMLITE_LLVM_ASSERTIONS_STATE=${LLVMLITE_LLVM_ASSERTIONS_UNKNOWN})
    message(STATUS "LLVM assertions state detected as 'unknown'")
else()
    if(LLVM_ENABLE_ASSERTIONS)
        add_definitions(
        -DLLVMLITE_LLVM_ASSERTIONS_STATE=${LLVMLITE_LLVM_ASSERTIONS_ON})
        message(STATUS "LLVM assertions state detected as 'on'")
    else()
        add_definitions(
        -DLLVMLITE_LLVM_ASSERTIONS_STATE=${LLVMLITE_LLVM_ASSERTIONS_OFF})
        message(STATUS "LLVM assertions state detected as 'off'")
    endif()
endif()


# Setup and report on linkage against LLVM libraries
message(STATUS "LLVM target link libraries: ${llvm_libs}")
target_link_libraries(llvmlite ${llvm_libs})


# -flto and --exclude-libs allow removal of unused parts of LLVM
# TODO: these options are just set, they should really be tested for
# suitability.
if(UNIX AND NOT APPLE)
    set(FORCED_LINK_FLAGS "-Wl,--exclude-libs,ALL -Wl,--no-undefined")
    # If FLTO at compile time, it's also needed at link time. There's a good
    # chance it's carried in the C++ flags and will appear in the driver link
    # mode, but just to make sure.
    if (LLVMLITE_FLTO)
        STRING(APPEND FORCED_LINK_FLAGS " -flto")
    endif()
    set_property(TARGET llvmlite APPEND_STRING PROPERTY LINK_FLAGS
                 "${FORCED_LINK_FLAGS}")
elseif(APPLE)
# On Darwin only include the LLVMPY symbols required and exclude
# everything else.
    set(LLVM_EXPORTED_SYMBOLS "-Wl,-exported_symbol,_LLVMPY_*")
    set_property(TARGET llvmlite APPEND_STRING PROPERTY LINK_FLAGS
                 "${LLVM_EXPORTED_SYMBOLS}")
endif()
