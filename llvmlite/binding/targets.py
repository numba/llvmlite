from __future__ import print_function, absolute_import
from ctypes import POINTER, c_char_p
from . import ffi


def get_default_triple():
    with ffi.OutputString() as out:
        ffi.lib.LLVMPY_GetDefaultTargetTriple(out)
        return str(out)


def create_target_data(strrep):
    return TargetData(ffi.lib.LLVMPY_CreateTargetData(strrep.encode('utf8')))


class TargetData(ffi.ObjectRef):
    def __str__(self):
        with ffi.OutputString() as out:
            ffi.lib.LLVMPY_CopyStringRepOfTargetData(self, out)
            return str(out)

    def close(self):
        ffi.lib.LLVMPY_DisposeTargetData(self)

# ============================================================================
# FFI

ffi.lib.LLVMPY_GetDefaultTargetTriple.argtypes = [POINTER(c_char_p)]

ffi.lib.LLVMPY_CreateTargetData.argtypes = [c_char_p]
ffi.lib.LLVMPY_CreateTargetData.restype = ffi.LLVMTargetDataRef

ffi.lib.LLVMPY_CopyStringRepOfTargetData.argtypes = [
    ffi.LLVMTargetDataRef,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_DisposeTargetData = [
    ffi.LLVMTargetDataRef,
]

ffi.lib.LLVMPY_AddTargetData.argtypes = [ffi.LLVMTargetDataRef,
                                         ffi.LLVMPassManagerRef]

