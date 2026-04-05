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

# Set C++ ABI based on architecture
# x86_64 llvmdev used manylinux2014 image, which uses old ABI, 
# aarch64 uses manylinux_2_28 image, which uses new ABI
# llvmlite now uses manylinux_2_28 image for both architectures, which uses new ABI
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    # set old ABI for x86_64
    export CXXFLAGS="-D_GLIBCXX_USE_CXX11_ABI=0 ${CXXFLAGS}"
fi

# Build wheel
distdir=$outputdir/dist_$(uname -m)_$pyver
rm -rf $distdir
python setup.py bdist_wheel -d $distdir

# Audit wheel
cd $distdir
auditwheel --verbose repair *.whl

cd wheelhouse
ls
