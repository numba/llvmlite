#!/bin/bash

set -ex

source activate $CONDA_ENV

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
