"""
A collection of analysis utils
"""

from __future__ import absolute_import, print_function

from ctypes import POINTER, c_char_p, c_int

from llvmlite import ir
from . import ffi
from .module import parse_assembly


def get_function_cfg(func, show_inst=True):
    """Return a string of the control-flow graph of the function in DOT
    format. If the input `func` is not a materialized function, the module
    containing the function is parsed to create an actual LLVM module.
    The `show_inst` flag controls whether the instructions of each block
    are printed.
    """
    if isinstance(func, ir.Function):
        mod = parse_assembly(str(func.module))
        func = mod.get_function(func.name)

    # Assume func is a materialized function
    with ffi.OutputString() as dotstr:
        ffi.lib.LLVMPY_WriteCFG(func, dotstr, show_inst)
        return str(dotstr)


# Ctypes binding
ffi.lib.LLVMPY_WriteCFG.argtypes = [ffi.LLVMValueRef, POINTER(c_char_p), c_int]
