#!/bin/bash

set -ex

#TODO: These should come from cbc.yaml?
if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    if [[ $build_platform == osx-arm64 ]]; then
        export MACOSX_DEPLOYMENT_TARGET=11.1
    else
        export MACOSX_DEPLOYMENT_TARGET=10.15
    fi
fi

export PYTHONNOUSERSITE=1

# This is Numba channel specific: enables static linking of stdlibc++
export LLVMLITE_CXX_STATIC_LINK=1

$PYTHON -m pip install --no-index --no-deps --no-build-isolation -vv -e .
