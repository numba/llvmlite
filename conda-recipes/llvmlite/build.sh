
# If available, enable newer toolset on old RH / CentOS machines
toolset=/opt/rh/devtoolset-2

if [ -d $toolset ]; then
    . /opt/rh/devtoolset-2/enable
    export CC=gcc
    export CXX=g++
fi

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.9
fi

export PYTHONNOUSERSITE=1

python setup.py build --force
python setup.py install
