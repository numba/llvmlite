
# If available, enable newer toolset on old RH / CentOS machines
toolset=/opt/rh/devtoolset-2

if [ -d $toolset ]; then
    # Use modified script to enable the toolset, as the original script
    # assumes Python 2
    . ./conda-recipes/llvmlite-jenkins/enable_devtoolset.sh
fi

# If there is a system LLVM install of 3.5 or higher, prefer it over llvmdev
# as it is synchronized with the system's libstdc++.
llvm_config_candidate=/usr/bin/llvm-config

if [ -x ${llvm_config_candidate} \
     -a "$(${llvm_config_candidate} --version)" \> "3.5" ]
then export LLVM_CONFIG=${llvm_config_candidate}
fi

export PYTHONNOUSERSITE=1

python setup.py build --force
python setup.py install
