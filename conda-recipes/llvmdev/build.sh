./configure \
    --enable-pic \
    --enable-optimized \
    --disable-docs \
    --enable-targets=host \
    --disable-terminfo \
    --disable-libedit \
    --prefix=$PREFIX \
    --with-python=$SYS_PYTHON

make -j4 libs-only
make install-libs
