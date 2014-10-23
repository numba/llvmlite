
import os
import sys


# This module must be importable without loading the binding, to avoid
# bootstrapping issues in setup.py.

def get_library_name():
    """
    Return the name of the llvmlite shared library file.
    """
    if os.name == 'posix':
        if sys.platform == 'darwin':
            return 'libllvmlite.dylib'
        else:
            return 'libllvmlite.so'
    else:
        assert os.name == 'nt'
        return 'llvmlite.dll'
