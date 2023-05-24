from . import ffi
from ctypes import c_char_p, c_uint64
from .common import _encode_string

def getDeviceForFile(path):
    cp = _encode_string(path)
    return ffi.lib.LLVMPY_GetDeviceForFile(cp)

def getFileIdForFile(path):
    cp = _encode_string(path)
    return ffi.lib.LLVMPY_GetFileIdForFile(cp)

ffi.lib.LLVMPY_GetDeviceForFile.argtypes = [c_char_p]
ffi.lib.LLVMPY_GetDeviceForFile.restype  = c_uint64

ffi.lib.LLVMPY_GetFileIdForFile.argtypes = [c_char_p]
ffi.lib.LLVMPY_GetFileIdForFile.restype  = c_uint64
