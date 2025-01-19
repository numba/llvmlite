# curl -L https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.0/llvm-project-16.0.0.src.tar.xz -o llvm-project-16.0.0.tar.xz
# tar -xf llvm-project-16.0.0.tar.xz
cd .
cwd=$PWD
cd llvm-project-16.0.0.src
git apply ../MachoLLDpatch.path
cd ../

# cd $CONDA_PREFIX
mkdir lldbuild
cd lldbuild




# if [[ "$target_platform" == "linux-64" ]]; then
#   CMAKE_ARGS="${CMAKE_ARGS} -DLLVM_USE_INTEL_JITEVENTS=ON"
# fi

# if [[ "$CC_FOR_BUILD" != "" && "$CC_FOR_BUILD" != "$CC" ]]; then
#   CMAKE_ARGS="${CMAKE_ARGS} -DCROSS_TOOLCHAIN_FLAGS_NATIVE=-DCMAKE_C_COMPILER=$CC_FOR_BUILD;-DCMAKE_CXX_COMPILER=$CXX_FOR_BUILD;-DCMAKE_C_FLAGS=-O2;-DCMAKE_CXX_FLAGS=-O2;-DCMAKE_EXE_LINKER_FLAGS=-Wl,-rpath,${BUILD_PREFIX}/lib;-DCMAKE_MODULE_LINKER_FLAGS=;-DCMAKE_SHARED_LINKER_FLAGS=;-DCMAKE_STATIC_LINKER_FLAGS=;-DLLVM_INCLUDE_BENCHMARKS=OFF;"
#   CMAKE_ARGS="${CMAKE_ARGS} -DLLVM_HOST_TRIPLE=$(echo $HOST | sed s/conda/unknown/g) -DLLVM_DEFAULT_TARGET_TRIPLE=$(echo $HOST | sed s/conda/unknown/g)"
# fi

# # disable -fno-plt due to https://bugs.llvm.org/show_bug.cgi?id=51863 due to some GCC bug
# if [[ "$target_platform" == "linux-ppc64le" ]]; then
#   CFLAGS="$(echo $CFLAGS | sed 's/-fno-plt //g')"
#   CXXFLAGS="$(echo $CXXFLAGS | sed 's/-fno-plt //g')"
#   CMAKE_ARGS="${CMAKE_ARGS} -DFFI_INCLUDE_DIR=$PREFIX/include"
#   CMAKE_ARGS="${CMAKE_ARGS} -DFFI_LIBRARY_DIR=$PREFIX/lib"
# fi

# if [[ $target_platform == osx-arm64 ]]; then
#   CMAKE_ARGS="${CMAKE_ARGS} -DCMAKE_ENABLE_WERROR=FALSE"
# fi

cmake --fresh -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_RTTI=ON \
  -DLLVM_INCLUDE_TESTS=OFF \
  -DCMAKE_PREFIX_PATH=${CONDA_PREFIX} \
  -DCMAKE_LIBRARY_PATH=${CONDA_PREFIX}/lib \
  ${CMAKE_ARGS} \
  ${cwd}/llvm-project-16.0.0.src/lld
  # -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX \
  # -DCMAKE_INSTALL_LIBDIR=$CONDA_PREFIX/lib \
  # -DCMAKE_PREFIX_PATH=$CONDA_PREFIX \
  # -DLLVM_MAIN_INCLUDE_DIR=${CONDA_PREFIX}/include \
  # -DLLVM_OBJ_ROOT=${CONDA_PREFIX} \

make
# cmake --fresh --build .
# cmake --install .
