#!/bin/bash
set -e
cd /root
curl https://repo.anaconda.com/miniconda/$1 > mini3.sh
bash mini3.sh -b -f
source /root/miniconda3/bin/activate root

cd /root/llvmlite/buildscripts/manylinux2010
./configure_conda.sh
