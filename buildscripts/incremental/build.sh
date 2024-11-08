#!/bin/bash

set -x

source activate $CONDA_ENV

# need to build with Anaconda compilers on osx, but they conflict with llvmdev... bootstap
if [[ $(uname) == Darwin ]]; then
  # export LLVM_CONFIG explicitly as the one installed from llvmdev
  # in the build root env, the one in the bootstrap location needs to be ignored.
  export LLVM_CONFIG=$(ls $(which llvm-config))
  
  # Determine architecture
  ARCH=$(uname -m)
  if [[ "$ARCH" == "arm64" ]]; then
    CONDA_SUBDIR=osx-arm64
    # Bootstrap with ARM64 compiler
    conda create -y -p ${PWD}/bootstrap clangxx_osx-arm64
  else
    CONDA_SUBDIR=osx-64
    # Bootstrap with x86_64 compiler
    conda create -y -p ${PWD}/bootstrap clangxx_osx-64
  fi
  
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
  ${LLVM_CONFIG} --version
  export SDKROOT=${SDKPATH}

  # Set Darwin target based on architecture
  if [[ "$ARCH" == "arm64" ]]; then
    DARWIN_TARGET=arm64-apple-darwin20.0.0
  else
    DARWIN_TARGET=x86_64-apple-darwin13.4.0
  fi
fi

# Remove old deployment target override since we're using the one from env
if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    export MACOSX_DEPLOYMENT_TARGET  # Keep existing value
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