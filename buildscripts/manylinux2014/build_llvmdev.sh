#!/bin/bash

cd $(dirname $0)
source ./prepare_miniconda.sh $1
source /root/miniconda3/bin/activate buildenv
if [[ $ARCH == "aarch64" ]] ; then
    export BUILD_CHANNELS="-c conda-forge"
fi
echo "BUILD_CHANNELS:  $BUILD_CHANNELS"
conda-build $BUILD_CHANNELS /root/llvmlite/conda-recipes/llvmdev_manylinux2014 --output-folder=/root/llvmlite/docker_output
