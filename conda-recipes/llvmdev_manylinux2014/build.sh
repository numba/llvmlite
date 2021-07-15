#!/bin/bash

# based on https://github.com/AnacondaRecipes/llvmdev-feedstock/blob/master/recipe/build.sh

set -x

# This is the clang compiler prefix
DARWIN_TARGET=x86_64-apple-darwin13.4.0


declare -a _cmake_config
_cmake_config+=(-DCMAKE_INSTALL_PREFIX:PATH=${PREFIX})
_cmake_config+=(-DCMAKE_BUILD_TYPE:STRING=Release)
# The bootstrap clang I use was built with a static libLLVMObject.a and I trying to get the same here
# _cmake_config+=(-DBUILD_SHARED_LIBS:BOOL=ON)
_cmake_config+=(-DLLVM_ENABLE_ASSERTIONS:BOOL=ON)
_cmake_config+=(-DLINK_POLLY_INTO_TOOLS:BOOL=ON)
# Don't really require libxml2. Turn it off explicitly to avoid accidentally linking to system libs
_cmake_config+=(-DLLVM_ENABLE_LIBXML2:BOOL=OFF)
# Urgh, llvm *really* wants to link to ncurses / terminfo and we *really* do not want it to.
_cmake_config+=(-DHAVE_TERMINFO_CURSES=OFF)
# Sometimes these are reported as unused. Whatever.
_cmake_config+=(-DHAVE_TERMINFO_NCURSES=OFF)
_cmake_config+=(-DHAVE_TERMINFO_NCURSESW=OFF)
_cmake_config+=(-DHAVE_TERMINFO_TERMINFO=OFF)
_cmake_config+=(-DHAVE_TERMINFO_TINFO=OFF)
_cmake_config+=(-DHAVE_TERMIOS_H=OFF)
_cmake_config+=(-DCLANG_ENABLE_LIBXML=OFF)
_cmake_config+=(-DLIBOMP_INSTALL_ALIASES=OFF)
_cmake_config+=(-DLLVM_ENABLE_RTTI=OFF)
_cmake_config+=(-DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX")
_cmake_config+=(-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly)
_cmake_config+=(-DLLVM_INCLUDE_UTILS=ON) # for llvm-lit
# TODO :: It would be nice if we had a cross-ecosystem 'BUILD_TIME_LIMITED' env var we could use to
#         disable these unnecessary but useful things.
if [[ ${CONDA_FORGE} == yes ]]; then
  _cmake_config+=(-DLLVM_INCLUDE_TESTS=OFF)
  _cmake_config+=(-DLLVM_INCLUDE_DOCS=OFF)
  _cmake_config+=(-DLLVM_INCLUDE_EXAMPLES=OFF)
fi
# Only valid when using the Ninja Generator AFAICT
# _cmake_config+=(-DLLVM_PARALLEL_LINK_JOBS:STRING=1)
# What about cross-compiling targetting Darwin here? Are any of these needed?
if [[ $(uname) == Darwin ]]; then
  _cmake_config+=(-DCMAKE_OSX_SYSROOT=${SYSROOT_DIR})
  _cmake_config+=(-DDARWIN_macosx_CACHED_SYSROOT=${SYSROOT_DIR})
  _cmake_config+=(-DCMAKE_OSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET})
  _cmake_config+=(-DCMAKE_LIBTOOL=$(which ${DARWIN_TARGET}-libtool))
  _cmake_config+=(-DLD64_EXECUTABLE=$(which ${DARWIN_TARGET}-ld))
  _cmake_config+=(-DCMAKE_INSTALL_NAME_TOOL=$(which ${DARWIN_TARGET}-install_name_tool))
  # Once we are using our libc++ (not until llvm_build_final), it will be single-arch only and not setting
  # this causes link failures building the santizers since they respect DARWIN_osx_ARCHS. We may as well
  # save some compilation time by setting this for all of our llvm builds.
  _cmake_config+=(-DDARWIN_osx_ARCHS=x86_64)
elif [[ $(uname) == Linux ]]; then
  _cmake_config+=(-DLLVM_USE_INTEL_JITEVENTS=ON)
#  _cmake_config+=(-DLLVM_BINUTILS_INCDIR=${PREFIX}/lib/gcc/${cpu_arch}-${vendor}-linux-gnu/${compiler_ver}/plugin/include)
fi

# For when the going gets tough:
# _cmake_config+=(-Wdev)
# _cmake_config+=(--debug-output)
# _cmake_config+=(--trace-expand)
# CPU_COUNT=1

mkdir build
cd build

cmake -G'Unix Makefiles'     \
      "${_cmake_config[@]}"  \
      ..

ARCH=`uname -m`
if [ $ARCH == 'armv7l' ]; then # RPi need thread count throttling
    make -j2 VERBOSE=1
else
    make -j${CPU_COUNT} VERBOSE=1
fi

# From: https://github.com/conda-forge/llvmdev-feedstock/pull/53
make install || exit $?

cd ../test
../build/bin/llvm-lit -vv Transforms ExecutionEngine Analysis CodeGen/X86
