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

# Install llvmdev 20 and compiler toolchain for linux
# 
if [[ "$(uname)" == "Linux" ]]; then
    $CONDA_INSTALL numba/label/dev::llvmdev=20 gcc_linux-64=11 gxx_linux-64=11
else
    $CONDA_INSTALL numba/label/dev::llvmdev=20
fi

# Install dependencies for code coverage (codecov.io)
if [ "$RUN_COVERAGE" == "yes" ]; then $PIP_INSTALL codecov coveralls; fi
