#!/bin/bash
# Use this to make the llvmdev packages that are manylinux2010 compatible
srcdir=$( cd "$(dirname $0)/../.."  && pwd )
echo "srcdir=$srcdir"

echo "MINICONDA_FILE=$MINICONDA_FILE"
docker run -it -e "ARCH=$ARCH" -v $srcdir:/root/llvmlite quay.io/pypa/manylinux2014_${ARCH} ${PRECMD} /root/llvmlite/buildscripts/manylinux_2_17/$1 ${MINICONDA_FILE} $2
