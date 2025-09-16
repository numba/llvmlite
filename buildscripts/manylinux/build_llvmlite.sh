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
LLVMDEV_ARTIFACT_PATH=${3:-""}

ls -l /opt/python/$pyver/bin

conda create -y -n $envname
conda activate $envname
# Install llvmdev

if [ -n "$LLVMDEV_ARTIFACT_PATH" ] && [ -d "$LLVMDEV_ARTIFACT_PATH" ]; then
    conda install -y "$LLVMDEV_ARTIFACT_PATH"/llvmdev-*.conda --no-deps
else
    conda install -y -c defaults numba/label/llvm20-wheel::llvmdev=20 --no-deps
fi

# Prepend builtin Python Path
export PATH=/opt/python/$pyver/bin:$PATH

echo "Using python: $(which python)"

# Python 3.12+ won't have setuptools pre-installed
pip install setuptools

# Clean up
python setup.py clean

# Configure build via env vars
export LLVMLITE_PACKAGE_FORMAT="wheel"

# Build wheel
distdir=$outputdir/dist_$(uname -m)_$pyver
rm -rf $distdir
python setup.py bdist_wheel -d $distdir

# Audit wheel
cd $distdir
auditwheel --verbose repair *.whl

cd wheelhouse
ls
