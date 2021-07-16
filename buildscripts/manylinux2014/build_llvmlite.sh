#!/bin/bash
set -e

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
source activate $envname
# Install llvmdev

if [[ $ARCH == "aarch64" ]] ; then
    conda install -y numba/label/manylinux2014::llvmdev --no-deps
else
    conda install -y -c numba/label/manylinux2014 llvmdev
fi

# Prepend builtin Python Path
export PATH=/opt/python/$pyver/bin:$PATH

echo "Using python: $(which python)"

# Clean up
git clean -xdf llvmlite build
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
