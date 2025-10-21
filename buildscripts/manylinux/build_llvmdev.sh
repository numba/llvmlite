#!/bin/bash
# $1 is the miniconda download link
if [ -z "$1" ]; then
    echo "Error: Miniconda download link argument is required"
    exit 1
fi
set -xe
cd $(dirname $0)
source ./prepare_miniconda.sh $1
if [[ "$(uname -m)" == "aarch64" ]]; then
    # py-lief-0.16.4 causes tag errors on aarch64, related issue: https://github.com/conda/conda-build/issues/5665  
    conda create -n buildenv -y conda conda-build "py-lief<0.16"
else
    conda create -n buildenv -y conda conda-build
fi
conda activate buildenv
conda list
conda-build -c defaults /root/llvmlite/conda-recipes/llvmdev_for_wheel --output-folder=/root/llvmlite/docker_output
