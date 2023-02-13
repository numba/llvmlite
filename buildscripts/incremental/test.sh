#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

# Ensure that the documentation builds without warnings nor missing references
cd docs
make SPHINXOPTS=-Wn clean html

# Run test suite
cd ..
python --version

if [ "$WHEEL" == "yes" ]; then
    cd dist
    python -m llvmlite.tests -v
else
    python runtests.py -v
fi
if [ "$RUN_COVERAGE" == "yes" ]; then coverage run runtests.py; fi
