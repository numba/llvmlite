from ctypes import POINTER, c_char_p
from . import ffi


class ValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value.
    """

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)

    @property
    def module(self):
        """Only valid for global value
        """
        return ffi.lib.LLVMPY_GetGlobalParent(self)

    @property
    def name(self):
        return ffi.lib.LLVMPY_GetValueName(self)

# FFI

ffi.lib.LLVMPY_PrintValueToString.argtypes = [
    ffi.LLVMValueRef,
    POINTER(c_char_p)
]

ffi.lib.LLVMPY_GetGlobalParent.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetGlobalParent.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetValueName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetValueName.restype = c_char_p
