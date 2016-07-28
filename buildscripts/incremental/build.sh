#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

# Needed for LLVM on OS X
export MACOSX_DEPLOYMENT_TARGET=10.9

python setup.py build
