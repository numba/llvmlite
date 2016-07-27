#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -e -x


# Ensure that the documentation builds without warnings nor missing references
cd $TRAVIS_BUILD_DIR/docs
make SPHINXOPTS=-Wn clean html

# Run test suite
cd $TRAVIS_BUILD_DIR
python runtests.py -v
if [ "$RUN_COVERAGE" == "yes" ]; then coverage run runtests.py; fi
