#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

python setup.py build
