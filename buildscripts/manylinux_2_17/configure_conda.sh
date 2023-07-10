#!/bin/bash
# Setup miniconda environment that is compatible with manylinux2014 docker image
conda create -n buildenv -y conda conda-build anaconda-client
source /root/miniconda3/bin/activate buildenv
conda env list
conda install -y conda-build anaconda-client
