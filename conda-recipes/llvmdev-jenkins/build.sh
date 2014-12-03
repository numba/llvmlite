if [ -z "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # Enable devtoolset-2, a newer gcc toolchain
    . /opt/rh/devtoolset-2/enable
    # Statically link the standard C/C++ library, because
    # we are building on an old centos5 machine.
    export CC=gcc
    export CXX=g++
    # Linux
    ./configure \
        --enable-pic \
        --enable-optimized \
        --disable-docs \
        --enable-targets=host \
        --disable-terminfo \
        --disable-libedit \
        --prefix=$PREFIX \
        --with-python=$SYS_PYTHON

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

make -j4 libs-only
make install-libs

