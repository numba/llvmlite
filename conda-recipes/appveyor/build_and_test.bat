@rem This script will build and test llvmlite.
@echo on

conda config --add channels numba
conda create -q -n testenv python=%CONDA_PY% llvmdev
call activate testenv

%CMD_IN_ENV% python setup.py build
%CMD_IN_ENV% python runtests.py -v
