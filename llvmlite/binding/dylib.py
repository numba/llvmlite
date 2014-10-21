from __future__ import absolute_import, print_function
from ctypes import c_void_p, c_char_p

from . import ffi
from .common import _encode_string


def address_of_symbol(name):
    return ffi.lib.LLVMPY_SearchAddressOfSymbol(_encode_string(name))


def add_symbol(name, address):
    ffi.lib.LLVMPY_AddSymbol(_encode_string(name), c_void_p(address))

# ============================================================================
# FFI

ffi.lib.LLVMPY_AddSymbol.argtypes = [
    c_char_p,
    c_void_p,
]

ffi.lib.LLVMPY_SearchAddressOfSymbol.argtypes = [c_char_p]
ffi.lib.LLVMPY_SearchAddressOfSymbol.restype = c_void_p

