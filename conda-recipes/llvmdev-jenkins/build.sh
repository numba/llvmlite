CMAKE_COMMON_VARIABLES=" -DCMAKE_INSTALL_PREFIX=$PREFIX \
    -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD=host \
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_UTILS=OFF \
    -DLLVM_INCLUDE_DOCS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF \
    "

if [ -z "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # Linux
    # Enable devtoolset-2, a newer gcc toolchain
    . /opt/rh/devtoolset-2/enable
    # Statically link the standard C/C++ library, because
    # we are building on an old centos5 machine.
    export CC=gcc
    export CXX=g++

    mkdir build
    cd build
    cmake $CMAKE_COMMON_VARIABLES -DLLVM_USE_OPROFILE=ON ..

else
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.7
    ./configure \
        --enable-pic \
        --enable-optimized \
        --disable-docs \
        --enable-targets=host \
        --disable-terminfo \
        --disable-libedit \
        --prefix=$PREFIX \
        --with-python=$SYS_PYTHON \
        --enable-libcpp=yes

fi

make -j4
make install
