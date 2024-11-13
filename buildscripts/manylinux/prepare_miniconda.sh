#!/bin/bash
set -e
cd /root
curl -L -o mini3.sh $1
bash mini3.sh -b -f -p $HOME/miniconda3
echo "Miniconda installed"
source $HOME/miniconda3/bin/activate base
echo "Env activated"
cd /root/llvmlite/buildscripts/manylinux
conda create -n buildenv -y conda conda-build

