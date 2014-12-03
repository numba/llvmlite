if [ -z "$MACOSX_DEPLOYMENT_TARGET" ]; then
     # Enable devtoolset-2, a newer gcc toolchain
     . ./conda-recipes/llvmlite-jenkins/enable_devtoolset.sh
     # Statically link the standard C/C++ library, because
     # we are building on an old centos5 machine.
     export CC=gcc
     export CXX=g++
fi

# If there is a system LLVM install of 3.5 or higher, prefer it over llvmdev
# as it is synchronized with the system's libstdc++.

llvm_config_candidate=/usr/bin/llvm-config

if [ -x ${llvm_config_candidate} \
     -a "$(${llvm_config_candidate} --version)" \> "3.5" ]
then export LLVM_CONFIG=${llvm_config_candidate}
fi

export PYTHONNOUSERSITE=1

python setup.py build
python setup.py install
