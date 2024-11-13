#!/bin/bash
set -xe
# Use this to make the llvmdev packages that are manylinux2010 compatible
srcdir=$( cd "$(dirname $0)/../.."  && pwd )
echo "srcdir=$srcdir"

echo "MINICONDA_FILE=$MINICONDA_FILE"
docker run --rm -it -e "ARCH=$ARCH" -v $srcdir:/root/llvmlite quay.io/pypa/${MANYLINUX_IMAGE} ${PRECMD} /root/llvmlite/buildscripts/manylinux/$1 ${MINICONDA_FILE} $2
