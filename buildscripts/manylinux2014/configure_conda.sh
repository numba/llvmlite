#!/bin/bash
# Setup miniconda environment that is compatible with manylinux2014 docker image
if [[ $ARCH == "aarch64" ]] ; then
    conda create -n buildenv -y conda conda-build anaconda-client libgcc-ng=7.5.0 libstdcxx-ng=7.5.0
else
    conda create -n buildenv -y conda conda-build anaconda-client
fi
source /root/miniconda3/bin/activate buildenv
conda env list
conda install -y conda-build anaconda-client

if [[ $ARCH == "aarch64" ]] ; then
    # # Pin conda and conda-build versions that are known to be compatible
    echo "libgcc-ng=7" >> /root/miniconda3/conda-meta/pinned
    echo "libstdcxx-ng=7" >> /root/miniconda3/conda-meta/pinned
    # echo "conda-build ==3.0.9" >> /root/miniconda3/conda-meta/pinned
fi
