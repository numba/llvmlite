#!/bin/bash
set -ex

cd $(dirname $0)
source ./prepare_miniconda.sh $1


# Move to source root
cd ../..
sourceroot=$(pwd)

# Make conda environmant for llvmdev
pyver=$2
envname="llvmbase"
outputdir="/root/llvmlite/docker_output"

ls -l /opt/python/$pyver/bin

conda create -y -n $envname 
conda activate $envname
# Install llvmdev

if [[ $(uname -m) == "aarch64" ]] ; then
    conda install -y numba/label/manylinux_2_28::llvmdev --no-deps
elif [[ $(uname -m) == "x86_64" ]] ; then
    conda install -y numba/label/manylinux_2_17::llvmdev --no-deps
else
    echo "Error: Unsupported architecture: $(uname -m)"
    exit 1
fi

# Prepend builtin Python Path
export PATH=/opt/python/$pyver/bin:$PATH

echo "Using python: $(which python)"

# Python 3.12+ won't have setuptools pre-installed
pip install setuptools

# Clean up
python setup.py clean

# Build wheel
distdir=$outputdir/dist_$(uname -m)_$pyver
rm -rf $distdir
python setup.py bdist_wheel -d $distdir

# Audit wheel
cd $distdir
auditwheel --verbose repair *.whl

cd wheelhouse
ls


# Verify & Test
pip install *.whl
python -m llvmlite.tests -vb
