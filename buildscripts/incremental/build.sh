#!/bin/bash

set -x

source activate $CONDA_ENV

# Set up osx.
if [[ $(uname) == Darwin ]]; then
  if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    export MACOSX_DEPLOYMENT_TARGET=10.15
  fi
  export DARWIN_TARGET=x86_64-apple-darwin13.4.0

  # Use explicit SDK path if set, otherwise detect
  if [ -z "$SDKROOT" ]; then
    SDKPATH=$(xcrun --show-sdk-path)
  else
    SDKPATH=$SDKROOT
  fi
  export CONDA_BUILD_SYSROOT=${CONDA_BUILD_SYSROOT:-${SDKPATH}}
  SYSROOT_DIR=${CONDA_BUILD_SYSROOT}
  CFLAG_SYSROOT="--sysroot ${SYSROOT_DIR}"
  export SDKROOT=${SDKPATH}
fi

export PYTHONNOUSERSITE=1

# This is Numba channel specific: enables static linking of libstdc++
if [[ "$(uname)" != "Darwin" ]]; then
  export LLVMLITE_CXX_STATIC_LINK=1
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
