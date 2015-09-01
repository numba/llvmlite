if [ -z "$MACOSX_DEPLOYMENT_TARGET" ]; then
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

make -j4
make install
