#!/bin/bash
# Use this to make the llvmdev packages that are manylinux1 compatible
srcdir=$( cd "$(dirname $0)/../.."  && pwd )
echo "srcdir=$srcdir"

echo "MINICONDA_FILE=$MINICONDA_FILE"
docker run --rm -v $srcdir:/root/llvmlite quay.io/pypa/manylinux1_${ARCH} ${PRECMD} /root/llvmlite/buildscripts/manylinux1/$1 ${MINICONDA_FILE} $2

