from __future__ import print_function, absolute_import
from ctypes import c_int, c_char_p, POINTER
from . import ffi


def link_modules(dst, src, preserve):
    dst.verify()
    src.verify()
    with ffi.OutputString() as outerr:
        if ffi.lib.LLVMPY_LinkModules(dst, src, int(preserve), outerr):
            raise RuntimeError(str(outerr))


ffi.lib.LLVMPY_LinkModules.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMModuleRef,
    c_int,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_LinkModules.restype = c_int
