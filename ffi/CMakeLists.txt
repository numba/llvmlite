cmake_minimum_required(VERSION 3.13)

# This will define the name of the solution file in the build directory
project(llvmlite_ffi)

include(CheckIncludeFiles)
include(CheckLibraryExists)
include(CheckCXXCompilerFlag)
include(CMakePushCheckState)
# Work around llvm/llvm-project#83802 - LLVM's Findzstd.cmake uses variables
# that require including `GNUInstallDirs`, but it does not include it itself.
include(GNUInstallDirs)

set(CMAKE_CXX_STANDARD 17)

find_package(LLVM REQUIRED CONFIG)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

# NOTE: Keep this in sync with the version that llvmlite is declared to support
set(LLVMLITE_SUPPORTED_LLVM_VERSION_DEFAULT 20)

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
if(UNIX)
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

# RTTI handling: This is a little awkward, it's a 3-state variable so cannot be
# an option. The states are user defined as ON or OFF, or user has not set so
# inherit from LLVM. This part removes the `-fno-rtti` option from
# CMAKE_CXX_FLAGS if appropriate, `-fno-rtti` is then added back in later as
# a flag on the compilation target if the compiler supports it and no-RTTI was
# determined to be appropriate.
if(UNIX)
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
    separate_arguments(CMAKE_CXX_FLAGS_AS_LIST UNIX_COMMAND
                       "${CMAKE_CXX_FLAGS}")
    list(FILTER CMAKE_CXX_FLAGS_AS_LIST EXCLUDE REGEX "^${FLAG_NO_RTTI}$")
    string(JOIN " " CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS_AS_LIST})
    if(LLVMLITE_USE_RTTI_FLAG)
        if(NOT ${OLD_CMAKE_CXX_FLAGS} STREQUAL ${CMAKE_CXX_FLAGS})
            message(STATUS "-fno-rtti was removed from CXXFLAGS.")
        else()
            message(STATUS "-fno-rtti is not in CXXFLAGS, nothing to do.")
        endif()
    else()
        # check the flag works.
        check_cxx_compiler_flag(${FLAG_NO_RTTI} HAVE_FNO_RTTI)
        if (NOT HAVE_FNO_RTTI)
            message(FATAL_ERROR
            "Compiler must support ${FLAG_NO_RTTI} option if it is requested")
        endif()
    endif()
endif()

# Define the shared library
add_library(llvmlite SHARED assembly.cpp bitcode.cpp config.cpp core.cpp initfini.cpp
            module.cpp value.cpp executionengine.cpp type.cpp
            targets.cpp dylib.cpp linker.cpp object_file.cpp
            custom_passes.cpp orcjit.cpp memorymanager.cpp newpassmanagers.cpp)


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

# Apply no-RTTI flag if RTTI use is off, must happen after target definition
if(UNIX AND NOT LLVMLITE_USE_RTTI_FLAG)
    message(STATUS "Applying no-RTTI flag to llvmlite target: ${FLAG_NO_RTTI}")
    target_compile_options(llvmlite PRIVATE ${FLAG_NO_RTTI})
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
    # library, see https://github.com/numba/llvmlite/pull/1234 for discussion.
    set(LLVM_COMPONENTS mcjit
                        orcjit
                        OrcDebugging
                        AsmPrinter
                        AllTargetsCodeGens
                        AllTargetsAsmParsers)

    # Test build specific components, it's not known a priori whether these
    # components will exist in a given build. On some platforms the components
    # may not exist for good reason, e.g. IntelJITEvents won't exist on an
    # aarch64 build, and equally, a custom LLVM may have mangled out the
    # building of optional components or a packager may have split the llvm
    # build such that a component is declared as present but is actually missing
    # because it is in another package. Essentially, there's no real way of
    # knowing and so each component is probed to check whether the mapped
    # libname library exists by virtue of attempting a link.

    # NOTE: To future editors, if you are upgrading LLVM and struggling to link,
    # it could be because some component used by llvmlite has been renamed or
    # split into two or similar. To resolve this, run `nm` on all the archive
    # files in the LLVM build and grep for the missing symbols or vtable or
    # whatever the linker is complaining about. Then add the name of the
    # component that contains the missing item to either the list above if it
    # could reasonably exist in all builds, or the list below if it's likely
    # just some builds have the "new" component. Typically the "component" is
    # just the  name of the library without whatever the system considers as a
    # libname and the "LLVM" prefix e.g. component IntelJITEvents corresponds to
    # archive libLLVMIntelJITEvents.a. There are some "special"
    # pseudo-components that have much broader expansions but it's unlikely
    # these will be encountered.
    set(LLVM_BUILD_SPECIFIC_COMPONENTS IntelJITEvents)

    # This function checks for whether a specific LLVM component can be linked
    function(check_optional_component COMPONENT CURRENT_COMPONENTS)
        message(STATUS "Testing for LLVM component ${COMPONENT}")
        cmake_push_check_state(RESET)
        set(TEST_COMPONENT ${COMPONENT})
        llvm_map_components_to_libnames(TEST_COMPONENT_LIB ${TEST_COMPONENT})
        set(CMAKE_REQUIRED_LIBRARIES ${TEST_COMPONENT_LIB})
        # Need a per-component name to make sure the cached value from previous
        # run isn't reused, it also makes the STATUS output more clear.
        set(TMP_HAVE_COMPONENT "HAVE_COMPONENT:${COMPONENT}")
        check_cxx_source_compiles("int main(void){return 0;}"
                                  ${TMP_HAVE_COMPONENT})
        cmake_pop_check_state()
        if (${TMP_HAVE_COMPONENT})
            list(APPEND CURRENT_COMPONENTS ${TEST_COMPONENT})
        endif()
        # write back into caller scope
        set(LLVM_COMPONENTS ${CURRENT_COMPONENTS} PARENT_SCOPE)
    endfunction()

    # check each build specific component, if it's available it will be added to
    # LLVM_COMPONENTS.
    foreach(COMPONENT IN LISTS LLVM_BUILD_SPECIFIC_COMPONENTS)
        check_optional_component(${COMPONENT} "${LLVM_COMPONENTS}")
    endforeach()

    # Map known components to library names for linkage
    llvm_map_components_to_libnames(llvm_libs ${LLVM_COMPONENTS})
    message(STATUS "LLVM_COMPONENTS: ${LLVM_COMPONENTS}")
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
    set(FORCED_LINK_FLAGS "-Wl,-exported_symbol,_LLVMPY_*")
    if (LLVMLITE_FLTO)
        STRING(APPEND FORCED_LINK_FLAGS " -flto")
    endif()
    set_property(TARGET llvmlite APPEND_STRING PROPERTY LINK_FLAGS
                 "${FORCED_LINK_FLAGS}")
endif()
