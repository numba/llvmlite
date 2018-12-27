#!/bin/bash

./prepare_miniconda.sh

conda build /root/llvmlite/conda-recipes/llvmdev_manylinux1 --output-folder=/root/llvmlite/docker_output
