from __future__ import print_function, absolute_import
from ctypes import c_int, c_char_p, POINTER
from . import ffi


def link_modules(dst, src):
    dst.verify()
    src.verify()
    if ffi.lib.LLVMPY_LinkModules(dst, src):
        raise RuntimeError("linking modules failed")


ffi.lib.LLVMPY_LinkModules.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMModuleRef,
    c_int,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_LinkModules.restype = c_int
