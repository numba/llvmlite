mkdir build
cd build

if [[ "$CONDA_BUILD_CROSS_COMPILATION" == "1" ]]; then
    CMAKE_ARGS="$CMAKE_ARGS -DLLVM_CONFIG_PATH=$BUILD_PREFIX/bin/llvm-config -DLLVM_TABLEGEN_EXE=$BUILD_PREFIX/bin/llvm-tblgen"
fi

cmake -G Ninja \
  -DCMAKE_INSTALL_PREFIX=$PREFIX \
  -DCMAKE_INSTALL_LIBDIR=$PREFIX/lib \
  -DCMAKE_PREFIX_PATH=$PREFIX \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_RTTI=ON \
  -DLLVM_INCLUDE_TESTS=OFF \
  -DLLVM_OBJ_ROOT=${PREFIX} \
  -DLLVM_MAIN_INCLUDE_DIR=${PREFIX}/include \
  ${CMAKE_ARGS} \
  ../lld

cmake --build . -- -j${CPU_COUNT}
cmake --install .
