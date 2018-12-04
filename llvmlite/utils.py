
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

def get_hello_pass_library():
    """
    Return the name of the hello pass library
    """
    if os.name == 'posix':
        if sys.platform == 'darwin':
            return 'libLLVMPYHello.dylib'
        else:
            return 'libLLVMPYHello.so'
    else:
        assert os.name == 'nt'
        return 'LLVMPYHello.dll'

def get_library_files():
    """
    Return the names of shared library files needed for this platform.
    """
    files = [get_library_name(), get_hello_pass_library()]
    if os.name == 'nt':
        files.extend(['msvcr120.dll', 'msvcp120.dll'])
    return files
