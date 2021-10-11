#!/bin/bash

set -x

source activate $CONDA_ENV

# need to build with Anaconda compilers on osx, but they conflict with llvmdev... bootstap
if [[ $(uname) == Darwin ]]; then
  # export LLVM_CONFIG explicitly as the one installed from llvmdev
  # in the build root env, the one in the bootstrap location needs to be ignored.
  export LLVM_CONFIG=$(ls $(which llvm-config))
  # now bootstrap the toolchain for building
  conda create -y -p ${PWD}/bootstrap clangxx_osx-64
  SRC_DIR=${PWD}
  export PATH=${SRC_DIR}/bootstrap/bin:${PATH}
  CONDA_PREFIX=${SRC_DIR}/bootstrap \
    . ${SRC_DIR}/bootstrap/etc/conda/activate.d/*
  SDKPATH=$(xcrun --show-sdk-path)
  export CONDA_BUILD_SYSROOT=${CONDA_BUILD_SYSROOT:-${SDKPATH}}
  export CXXFLAGS=${CFLAGS}" -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
  export CFLAGS=${CFLAGS}" -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
  SYSROOT_DIR=${CONDA_BUILD_SYSROOT}
  CFLAG_SYSROOT="--sysroot ${SYSROOT_DIR}"
  ${LLVM_CONFIG} --version
  export SDKROOT=${SDKPATH}
fi

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.9
fi

if [[ ${MACOSX_DEPLOYMENT_TARGET} == 10.9 ]]; then
  DARWIN_TARGET=x86_64-apple-darwin13.4.0
fi


# Make sure any error below is reported as such
set -v -e

if [ "$WHEEL" == "yes" ]; then
  conda install wheel
  python setup.py bdist_wheel
  pip install dist/*.whl
else
  python setup.py build
fi
