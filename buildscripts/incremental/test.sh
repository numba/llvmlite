#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

# Run test suite

python --version

if [ "$OPAQUE_POINTERS" == "yes" ]; then
    export LLVMLITE_ENABLE_IR_LAYER_TYPED_POINTERS=0
    echo "Testing with IR layer opaque pointers enabled"
else
    echo "Testing with IR layer opaque pointers disabled"
fi

if [ "$WHEEL" == "yes" ]; then
    cd dist
    python -m llvmlite.tests -v
elif [ "$DIST_TEST" == "yes" ]; then
    LLVMLITE_DIST_TEST=1 python runtests.py -v
else
    python runtests.py -v
fi

if [ "$RUN_COVERAGE" == "yes" ]; then coverage run runtests.py; fi
