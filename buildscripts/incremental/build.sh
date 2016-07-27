#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -e -x

python setup.py build
