#!/bin/bash

set -e

CONDA_INSTALL="conda install -q -y"
PIP_INSTALL="pip install -q"

# Deactivate any environment
set +v
source deactivate
set -v
# Display root environment (for debugging)
conda list

if [ "$PYTHON" == "pypy" ]; then
    conda create -c gmarkall -n $CONDA_ENV -q -y pypy
else
    conda create -n $CONDA_ENV -q -y python=$PYTHON
fi

set +v
source activate $CONDA_ENV
set -v

$CONDA_INSTALL -c numba libxml2

# Install llvmdev (separate channel, for now)
if [ "$LLVM" == "16" ]; then
    # also install lld, not required when using the numba channel because the numba
    #  channel includes lld.
    $CONDA_INSTALL -c conda-forge llvmdev="16" lld="16" zstd-static
else
    # Install the compiler toolchain, for osx, bootstrapping needed
    # which happens in build.sh
    $CONDA_INSTALL -c numba llvmdev="15.*"
fi

if [[ $(uname) == Linux ]]; then
    # $CONDA_INSTALL gcc_linux-64 gxx_linux-64
    $CONDA_INSTALL -c conda-forge libstdcxx-ng
fi

# Install dependencies for code coverage (codecov.io)
if [ "$RUN_COVERAGE" == "yes" ]; then $PIP_INSTALL codecov coveralls; fi
