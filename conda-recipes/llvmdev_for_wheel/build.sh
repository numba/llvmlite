#!/bin/bash
# File is a copy of ../llvmdev/build.sh with changes to:
# - disable ZSTD


# based on https://github.com/AnacondaRecipes/llvmdev-feedstock/blob/master/recipe/build.sh

set -x

# Make osx work like linux.
sed -i.bak "s/NOT APPLE AND ARG_SONAME/ARG_SONAME/g" llvm/cmake/modules/AddLLVM.cmake
sed -i.bak "s/NOT APPLE AND NOT ARG_SONAME/NOT ARG_SONAME/g" llvm/cmake/modules/AddLLVM.cmake

mkdir build
cd build

export CPU_COUNT=4

CMAKE_ARGS="${CMAKE_ARGS} -DLLVM_ENABLE_PROJECTS=lld;compiler-rt"

if [[ "$target_platform" == "linux-64" ]]; then
  CMAKE_ARGS="${CMAKE_ARGS} -DLLVM_USE_INTEL_JITEVENTS=ON"
fi

if [[ "$CC_FOR_BUILD" != "" && "$CC_FOR_BUILD" != "$CC" ]]; then
  CMAKE_ARGS="${CMAKE_ARGS} -DCROSS_TOOLCHAIN_FLAGS_NATIVE=-DCMAKE_C_COMPILER=$CC_FOR_BUILD;-DCMAKE_CXX_COMPILER=$CXX_FOR_BUILD;-DCMAKE_C_FLAGS=-O2;-DCMAKE_CXX_FLAGS=-O2;-DCMAKE_EXE_LINKER_FLAGS=-Wl,-rpath,${BUILD_PREFIX}/lib;-DCMAKE_MODULE_LINKER_FLAGS=;-DCMAKE_SHARED_LINKER_FLAGS=;-DCMAKE_STATIC_LINKER_FLAGS=;-DLLVM_INCLUDE_BENCHMARKS=OFF;"
  CMAKE_ARGS="${CMAKE_ARGS} -DLLVM_HOST_TRIPLE=$(echo $HOST | sed s/conda/unknown/g) -DLLVM_DEFAULT_TARGET_TRIPLE=$(echo $HOST | sed s/conda/unknown/g)"
fi

# disable -fno-plt due to https://bugs.llvm.org/show_bug.cgi?id=51863 due to some GCC bug
if [[ "$target_platform" == "linux-ppc64le" ]]; then
  CFLAGS="$(echo $CFLAGS | sed 's/-fno-plt //g')"
  CXXFLAGS="$(echo $CXXFLAGS | sed 's/-fno-plt //g')"
  CMAKE_ARGS="${CMAKE_ARGS} -DFFI_INCLUDE_DIR=$PREFIX/include"
  CMAKE_ARGS="${CMAKE_ARGS} -DFFI_LIBRARY_DIR=$PREFIX/lib"
fi

if [[ $target_platform == osx-arm64 ]]; then
  CMAKE_ARGS="${CMAKE_ARGS} -DCMAKE_ENABLE_WERROR=FALSE"
fi

cmake -DCMAKE_INSTALL_PREFIX="${PREFIX}" \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_LIBRARY_PATH="${PREFIX}" \
      -DLLVM_ENABLE_ZSTD=OFF \
      -DLLVM_ENABLE_LIBEDIT=OFF \
      -DLLVM_ENABLE_LIBXML2=OFF \
      -DLLVM_ENABLE_RTTI=OFF \
      -DLLVM_ENABLE_ASSERTIONS=ON \
      -DLLVM_ENABLE_TERMINFO=OFF \
      -DLLVM_INCLUDE_BENCHMARKS=OFF \
      -DLLVM_INCLUDE_DOCS=OFF \
      -DLLVM_INCLUDE_EXAMPLES=OFF \
      -DLLVM_INCLUDE_GO_TESTS=OFF \
      -DLLVM_INCLUDE_TESTS=ON \
      -DLLVM_INCLUDE_UTILS=ON \
      -DLLVM_INSTALL_UTILS=ON \
      -DLLVM_UTILS_INSTALL_DIR=libexec/llvm \
      -DLLVM_BUILD_LLVM_DYLIB=OFF \
      -DLLVM_LINK_LLVM_DYLIB=OFF \
      -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly \
      -DLLVM_ENABLE_FFI=ON \
      -DLLVM_ENABLE_Z3_SOLVER=OFF \
      -DLLVM_OPTIMIZED_TABLEGEN=ON \
      -DCMAKE_POLICY_DEFAULT_CMP0111=NEW \
      -DCOMPILER_RT_BUILD_BUILTINS=ON \
      -DCOMPILER_RT_ENABLE_IOS=OFF \
      -DCOMPILER_RT_BUILTINS_HIDE_SYMBOLS=OFF \
      -DCOMPILER_RT_BUILD_LIBFUZZER=OFF \
      -DCOMPILER_RT_BUILD_CRT=OFF \
      -DCOMPILER_RT_BUILD_MEMPROF=OFF \
      -DCOMPILER_RT_BUILD_PROFILE=OFF \
      -DCOMPILER_RT_BUILD_SANITIZERS=OFF \
      -DCOMPILER_RT_BUILD_XRAY=OFF \
      -DCOMPILER_RT_BUILD_GWP_ASAN=OFF \
      -DCOMPILER_RT_BUILD_ORC=OFF \
      -DCOMPILER_RT_INCLUDE_TESTS=OFF \
      ${CMAKE_ARGS} \
      -GNinja \
      ../llvm


ninja -j${CPU_COUNT}

ninja install

if [[ "${target_platform}" == "linux-64" ]]; then
    export TEST_CPU_FLAG="-mcpu=haswell"
else
    export TEST_CPU_FLAG=""
fi

if [[ "$CONDA_BUILD_CROSS_COMPILATION" != "1" ]]; then

  echo "Testing on ${target_platform}"
  # bin/opt -S -vector-library=SVML $TEST_CPU_FLAG -O3 $RECIPE_DIR/numba-3016.ll | bin/FileCheck $RECIPE_DIR/numba-3016.ll || exit $?

  if [[ "$target_platform" == linux* ]]; then
    ln -s $(which $CC) $BUILD_PREFIX/bin/gcc

    # These tests tests permission-based behaviour and probably fail because of some
    # filesystem-related reason. They are sporadic failures and don't seem serious so they're excluded.
    # Note that indents would introduce spaces into the environment variable
    export LIT_FILTER_OUT='tools/llvm-ar/error-opening-permission.test|'\
'tools/llvm-dwarfdump/X86/output.s|'\
'tools/llvm-ifs/fail-file-write.test|'\
'tools/llvm-ranlib/error-opening-permission.test|'\
'ExecutionEngine/Interpreter/intrinsics.ll'
  fi

  if [[ "$target_platform" == osx-* ]]; then
    # This failure seems like something to do with the output format of ls -lu
    # and looks harmless
    export LIT_FILTER_OUT='tools/llvm-objcopy/ELF/strip-preserve-atime.test|'\
'ExecutionEngine/Interpreter/intrinsics.ll'
  fi

  cd ../llvm/test
  ${PYTHON} ../../build/bin/llvm-lit -vv --ignore-fail Transforms ExecutionEngine Analysis CodeGen/X86
fi

