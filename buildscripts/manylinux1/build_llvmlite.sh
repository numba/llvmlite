#!/bin/bash
set -xe 

cd $(dirname $0)
source ./prepare_miniconda.sh $1


# Move to source root
cd ../..

# Make conda environmant for llvmdev
pyver=$2
envname="llvmbase"
outputdir="/root/llvmlite/docker_output"

conda create -y -n $envname
source activate $envname
# Install llvmdev
conda install -y -c numba/label/manylinux1 llvmdev

# Prepend builtin Python Path
export PATH=/opt/python/$pyver/bin:$PATH

# Build wheel
distdir=$outputdir/dist_$(uname -m)_$pyver
python setup.py bdist_wheel -d $distdir

# Audit wheel
cd $distdir
auditwheel repair *.whl 

cd wheelhouse
ls
