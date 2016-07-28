#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

# Ensure that the documentation builds without warnings nor missing references
cd docs
make SPHINXOPTS=-Wn clean html

# Run test suite
cd ..
python runtests.py -v
if [ "$RUN_COVERAGE" == "yes" ]; then coverage run runtests.py; fi
