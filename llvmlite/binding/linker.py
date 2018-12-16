from __future__ import print_function, absolute_import
from ctypes import c_int, c_char_p, POINTER
from . import ffi


def link_modules(dst, src):
    with ffi.OutputString() as outerr:
        err = ffi.lib.LLVMPY_LinkModules(dst, src, outerr)
        # The underlying module was destroyed
        src.detach()
        if err:
            raise RuntimeError(str(outerr))


ffi.lib.LLVMPY_LinkModules.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_LinkModules.restype = c_int
