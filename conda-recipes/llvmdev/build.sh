CMAKE_COMMON_VARIABLES=" -DCMAKE_INSTALL_PREFIX=$PREFIX \
    -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD=host \
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_UTILS=OFF \
    -DLLVM_INCLUDE_DOCS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF \
    -DLLVM_ENABLE_TERMINFO=OFF \
    "

platform='unknown'
unamestr="$(uname)"
machine="$(uname -m)"

if [[ "$unamestr" == 'Linux' ]]; then
    platform='linux'
elif [[ "$unamestr" == 'FreeBSD' ]]; then
    platform='freebsd'
elif [[ "$unamestr" == 'Darwin' ]]; then
    platform='osx'
fi

# Note you may need to enable RH devtoolset-2 if building on an
# old RH or CentOS system

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.9
fi

# Use CMake-based build procedure
mkdir build
cd build
if [ "$platform" == 'linux' -a "$machine" != 'armv7l' ]; then
    cmake $CMAKE_COMMON_VARIABLES -DLLVM_USE_OPROFILE=ON ..
else
    cmake $CMAKE_COMMON_VARIABLES ..
fi

make -j8
make install
