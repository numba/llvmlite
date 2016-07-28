#!/bin/bash

source activate $CONDA_ENV

# Make sure any error below is reported as such
set -v -e

if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    # OSX needs 10.7 or above with libc++ enabled
    export MACOSX_DEPLOYMENT_TARGET=10.9
fi

python setup.py build
