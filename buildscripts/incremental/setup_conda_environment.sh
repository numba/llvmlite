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
$CONDA_INSTALL -c numba llvmdev="10.0*"

# Install the compiler toolchain, for osx, bootstrapping needed
# which happens in build.sh
if [[ $(uname) == Linux ]]; then
$CONDA_INSTALL gcc_linux-64 gxx_linux-64
fi

# Install enum34 for Python < 3.4 and PyPy, and install dependencies for
# building the docs.
if [ "$PYTHON" == "pypy" ]; then
  $CONDA_INSTALL zlib # pypy has no conda-level zlib linkage
  python -m ensurepip
  $PIP_INSTALL enum34
  # Sphinx 1.5.4 has a bug.
  $PIP_INSTALL sphinx==1.5.1 sphinx_rtd_theme pygments
else
  $CONDA_INSTALL sphinx sphinx_rtd_theme pygments
fi

# Install dependencies for code coverage (codecov.io)
if [ "$RUN_COVERAGE" == "yes" ]; then $PIP_INSTALL codecov coveralls; fi
