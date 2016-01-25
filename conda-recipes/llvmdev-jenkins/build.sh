CMAKE_COMMON_VARIABLES=" -DCMAKE_INSTALL_PREFIX=$PREFIX \
    -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD=host \
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_UTILS=OFF \
    -DLLVM_INCLUDE_DOCS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF \
    "

# If available, enable newer toolset on old RH / CentOS machines
toolset=/opt/rh/devtoolset-2

if [ -d $toolset ]; then
    . /opt/rh/devtoolset-2/enable
    export CC=gcc
    export CXX=g++
fi

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.7
fi

#     ./configure \
#         --enable-pic \
#         --enable-optimized \
#         --disable-docs \
#         --enable-targets=host \
#         --disable-terminfo \
#         --disable-libedit \
#         --prefix=$PREFIX \
#         --with-python=$SYS_PYTHON \
#         --enable-libcpp=yes

# Use CMake-based build procedure
mkdir build
cd build
cmake $CMAKE_COMMON_VARIABLES -DLLVM_USE_OPROFILE=ON ..

make -j4
make install
