#!/bin/bash
set -e
cd /root
curl -L $1 > mini3.sh
bash mini3.sh -b -f -p $HOME/miniconda3
source /root/miniconda3/bin/activate root

cd /root/llvmlite/buildscripts/manylinux_2_17
./configure_conda.sh
