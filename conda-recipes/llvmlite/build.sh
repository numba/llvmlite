# Note you may need to enable RH devtoolset-2 if building on an
# old RH or CentOS system

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.9
fi

export PYTHONNOUSERSITE=1
# Enables static linking of stdlibc++
export LLVMLITE_CXX_STATIC_LINK=1

python setup.py build --force
python setup.py install
