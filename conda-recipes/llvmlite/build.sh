#!/bin/bash

set -ex

#TODO: These should come from cbc.yaml?
if [ -n "$MACOSX_DEPLOYMENT_TARGET" ]; then
    if [[ $build_platform == osx-arm64 ]]; then
        export MACOSX_DEPLOYMENT_TARGET=11.1
    else
        # OSX needs 10.15 or above for consistency with wheel builds
        export MACOSX_DEPLOYMENT_TARGET=10.15
    fi
fi

export PYTHONNOUSERSITE=1

# This is Numba channel specific: enables static linking of stdlibc++
if [[ "$(uname)" != "Darwin" ]]; then
    export LLVMLITE_CXX_STATIC_LINK=1
fi
# This is Numba channel specific: declare this as a conda package
export LLVMLITE_PACKAGE_FORMAT="conda"

$PYTHON -m pip install --no-index --no-deps --no-build-isolation -vv .
