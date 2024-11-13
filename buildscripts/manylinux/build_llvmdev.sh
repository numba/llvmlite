#!/bin/bash
set -xe
cd $(dirname $0)
source ./prepare_miniconda.sh $1
# make conda-build env t
conda create -n buildenv -y conda conda-build
conda activate buildenv
conda list
echo "BUILD_CHANNELS:  $BUILD_CHANNELS"
conda-build $BUILD_CHANNELS /root/llvmlite/conda-recipes/llvmdev_manylinux --output-folder=/root/llvmlite/docker_output
