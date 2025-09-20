#!/bin/bash

set -ex

source activate $CONDA_ENV

# need to build with Anaconda compilers on osx, but they conflict with
# llvmdev... bootstrap
if [[ $(uname) == Darwin ]]; then
  # Set conda subdir and bootstrap with x86_64 compiler
  CONDA_SUBDIR=osx-64
  conda create -y -p ${PWD}/bootstrap clangxx_osx-64

  SRC_DIR=${PWD}
  export PATH=${SRC_DIR}/bootstrap/bin:${PATH}
  CONDA_PREFIX=${SRC_DIR}/bootstrap \
    . ${SRC_DIR}/bootstrap/etc/conda/activate.d/*

  # Use explicit SDK path if set, otherwise detect
  if [ -z "$SDKROOT" ]; then
    SDKPATH=$(xcrun --show-sdk-path)
  else
    SDKPATH=$SDKROOT
  fi
  export CONDA_BUILD_SYSROOT=${CONDA_BUILD_SYSROOT:-${SDKPATH}}

  # Set minimum deployment target if not already set
  if [ -z "$MACOSX_DEPLOYMENT_TARGET" ]; then
    export MACOSX_DEPLOYMENT_TARGET=11.0
  fi

  export CXXFLAGS=${CFLAGS}" -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
  export CFLAGS=${CFLAGS}" -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET}"
  SYSROOT_DIR=${CONDA_BUILD_SYSROOT}
  CFLAG_SYSROOT="--sysroot ${SYSROOT_DIR}"
  export SDKROOT=${SDKPATH}

  DARWIN_TARGET=x86_64-apple-darwin13.4.0
fi

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    export MACOSX_DEPLOYMENT_TARGET
fi

# This is Numba channel specific: enables static linking of libstdc++
if [[ "$(uname)" != "Darwin" ]]; then
  export LLVMLITE_CXX_STATIC_LINK=1
fi

# Make sure any error below is reported as such
set -exv

if [ "$WHEEL" == "yes" ]; then
  conda install wheel
  python setup.py bdist_wheel
  pip install dist/*.whl
else
  python setup.py build
fi
