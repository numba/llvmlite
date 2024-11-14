#!/bin/bash
# $1 is the filename of the script to run inside docker.
#    The file must exist in buildscripts/manylinux/.
# $2 is the python version name in /opt/python of the manylinux docker image.
#    Only used for build_llvmlite.sh.
# Check if required parameters are provided
if [ -z "$1" ] ; then
    echo "Error: Missing required parameters"
    echo "Usage: $0 <script-filename> [<python-version>]"
    exit 1
fi
set -xe
# Use this to make the llvmdev packages that are manylinux compatible
SRCDIR=$( cd "$(dirname $0)/../.."  && pwd )
echo "SRCDIR=$SRCDIR"

echo "MINICONDA_FILE=$MINICONDA_FILE"
# Ensure the latest docker image
IMAGE_URI="quay.io/pypa/${MANYLINUX_IMAGE}:latest"
docker pull $IMAGE_URI
docker run --rm -it -v $SRCDIR:/root/llvmlite $IMAGE_URI ${PRECMD} /root/llvmlite/buildscripts/manylinux/$1 ${MINICONDA_FILE} $2
