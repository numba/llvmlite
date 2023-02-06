#!/bin/sh

set -eux

# Since LLVM to is too heavy weight to build, we install a copy using conda
# that's been build against the manylinux_2_X image we're going to build
# against. Now, neither conda nor cibuildwheel are going to enjoy this process,
# so we're going to install the conda package into a directory and then reach
# into that directory and carefully drag out LLVM using `llvm-config` as the
# only reference point. Since everything is going to be statically linked, we
# don't care about anything from this conda environment getting copied into the
# final output as the linker will effectively do that for us.

if [ -d "$HOME/miniconda3" ]; then
	rm -rf "$HOME/miniconda3"
fi

unamestr="$(uname)"
if [ "$unamestr" = 'Linux' ]; then
	curl -L -o miniconda.sh "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-$(uname -m).sh"
	chmod +x miniconda.sh
	bash ./miniconda.sh -b

	"$HOME/miniconda3/bin/conda" install -q -y numba/label/manylinux2014::llvmdev=14
elif [ "$unamestr" = 'Darwin' ]; then
	curl -L -o miniconda.sh "https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-$(uname -m).sh"
	chmod +x miniconda.sh
	bash ./miniconda.sh -b

	"$HOME/miniconda3/bin/conda" install -q -y numba::llvmdev=14
else
	echo Error
	exit 1
fi
