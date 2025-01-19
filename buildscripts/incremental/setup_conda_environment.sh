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
# Clean up any left-over from a previous build
# (note workaround for https://github.com/conda/conda/issues/2679:
#  `conda env remove` issue)
conda remove --all -q -y -n $CONDA_ENV
# Scipy, CFFI, jinja2 and IPython are optional dependencies, but exercised in the test suite
if [ "$PYTHON" == "pypy" ]; then
    conda create -c gmarkall -n $CONDA_ENV -q -y pypy
else
    conda create -n $CONDA_ENV -q -y python=$PYTHON
fi

set +v
source activate $CONDA_ENV
set -v

# Install llvmdev (separate channel, for now)
if [ "$LLVM" == "16" ]; then
    # also install lld, not required when using the numba channel because the numba
    #  channel includes lld.
    $CONDA_INSTALL -c conda-forge lld="16" llvmdev="16"
    export LLVMLITE_USE_CMAKE 1
else
    # Install the compiler toolchain, for osx, bootstrapping needed
    # which happens in build.sh
    $CONDA_INSTALL -c numba llvmdev="15.*"
fi

$CONDA_INSTALL -c numba libxml2 libcxx="12.*"

if [[ $(uname) == Linux ]]; then
    # $CONDA_INSTALL gcc_linux-64 gxx_linux-64
    $CONDA_INSTALL -c conda-forge libstdcxx-ng
fi

# Install dependencies for code coverage (codecov.io)
if [ "$RUN_COVERAGE" == "yes" ]; then $PIP_INSTALL codecov coveralls; fi
