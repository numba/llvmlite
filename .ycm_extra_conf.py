# YouCompleteMe (https://github.com/ycm-core/YouCompleteMe) configuration file
# that enables it to find the LLVM and Python includes from a conda
# environment, independent of the Conda environment location and Python and
# LLVM versions.

import os
import sys

from pathlib import Path

CONDA_PREFIX = os.environ['CONDA_PREFIX']
LLVMLITE_DIR = Path(__file__).parent
VER = sys.version_info
PYTHON_INCLUDE_NAME = f'python{VER.major}.{VER.minor}'

CONDA_INCLUDE_DIR = Path(CONDA_PREFIX, 'include')
PYTHON_INCLUDE_DIR = Path(CONDA_INCLUDE_DIR, PYTHON_INCLUDE_NAME)
FFI_DIR = Path(LLVMLITE_DIR, 'ffi')

flags = [
    # Include dirs
    f'-I{CONDA_INCLUDE_DIR}',
    f'-I{PYTHON_INCLUDE_DIR}',
    f'-I{FFI_DIR}',
    # C++ standard to which LLVM 14 is developed
    '-std=c++14',
    # Force language to C++ so that core.h is treated as C++
    '-x', 'c++',
]


# This function is called by YCM to obtain the config from this file.
def Settings(**kwargs):
    return {'flags': flags}


# Executing this configuration file standalone outside of YCM prints the
# settings to aid with debugging the configuration.
if __name__ == '__main__':
    print(Settings())
