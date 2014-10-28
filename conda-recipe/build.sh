export LLVM_CONFIG=/usr/bin/llvm-config

export PYTHONNOUSERSITE=1

python setup.py build
python setup.py install
