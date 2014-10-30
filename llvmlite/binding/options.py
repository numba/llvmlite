from . import ffi
from .common import _encode_string
from ctypes import c_char_p


def set_option(name, option):
    ffi.lib.LLVMPY_SetCommandLine(_encode_string(name),
                                  _encode_string(option))


ffi.lib.LLVMPY_SetCommandLine.argtypes = [c_char_p, c_char_p]
