#!/bin/bash
# $1 is the miniconda download link
if [ -z "$1" ]; then
    echo "Error: Miniconda download link argument is required"
    exit 1
fi
set -xe
cd $(dirname $0)
source ./prepare_miniconda.sh $1
conda create -n buildenv -y conda conda-build
conda activate buildenv
conda list
conda-build /root/llvmlite/conda-recipes/llvmdev_manylinux --output-folder=/root/llvmlite/docker_output
