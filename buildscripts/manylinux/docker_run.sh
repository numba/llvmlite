#!/bin/bash
set -xe
# Use this to make the llvmdev packages that are manylinux2010 compatible
srcdir=$( cd "$(dirname $0)/../.."  && pwd )
echo "srcdir=$srcdir"

echo "MINICONDA_FILE=$MINICONDA_FILE"
# Ensure the latest docker image
image="quay.io/pypa/${MANYLINUX_IMAGE}:latest"
docker pull $image
docker run --rm -it -e MANYLINUX_IMAGE=$MANYLINUX_IMAGE -v $srcdir:/root/llvmlite $image ${PRECMD} /root/llvmlite/buildscripts/manylinux/$1 ${MINICONDA_FILE} $2
