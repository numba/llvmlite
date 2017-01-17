#!/bin/bash

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
conda create -n $CONDA_ENV -q -y python=$PYTHON

set +v
source activate $CONDA_ENV
set -v

# Install llvmdev (separate channel, for now)
$CONDA_INSTALL -c numba llvmdev="3.9*"
# Install enum34 for Python < 3.4
if [ $PYTHON \< "3.4" ]; then $CONDA_INSTALL enum34; fi
# Install dependencies for building the docs
$CONDA_INSTALL sphinx sphinx_rtd_theme pygments
# Install dependencies for code coverage (codecov.io)
if [ "$RUN_COVERAGE" == "yes" ]; then $PIP_INSTALL codecov coveralls; fi
