from ctypes import POINTER, c_char_p, c_int

from . import ffi
from .common import _decode_string


_linkage_ct = iter(range(40))
_linkage_get = lambda: next(_linkage_ct)

LINKAGE = {
    'external': _linkage_get(),
    'available_externally': _linkage_get(),
    'linkonce_any': _linkage_get(),
    'linkonce_odr': _linkage_get(),
    'linkonce_odr_autohide': _linkage_get(),
    'appending': _linkage_get(),
    'internal': _linkage_get(),
    'private': _linkage_get(),
    'dllimport': _linkage_get(),
    'dllexport': _linkage_get(),
    'external_weak': _linkage_get(),
    'ghost': _linkage_get(),
    'common': _linkage_get(),
    'linker_private': _linkage_get(),
    'linker_private_weak': _linkage_get(),
}

_REVLINKAGE = dict((v, k) for k, v in LINKAGE.items())


class ValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value.
    """

    def __init__(self, ptr, module):
        self._module = module
        ffi.ObjectRef.__init__(self, ptr)

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)

    @property
    def module(self):
        """The module this value is defined in.
        """
        return self._module

    @property
    def name(self):
        return _decode_string(ffi.lib.LLVMPY_GetValueName(self))

    @name.setter
    def name(self, val):
        return _decode_string(ffi.lib.LLVMPY_SetValueName(self))

    @property
    def linkage(self):
        return _REVLINKAGE[ffi.lib.LLVMPY_GetLinkage(self)]

    @linkage.setter
    def linkage(self, value):
        ffi.lib.LLVMPY_SetLinkage(self, LINKAGE[value])

    @property
    def type(self):
        # XXX what does this return?
        return ffi.lib.LLVMPY_TypeOf(self)

# FFI

ffi.lib.LLVMPY_PrintValueToString.argtypes = [
    ffi.LLVMValueRef,
    POINTER(c_char_p)
]

ffi.lib.LLVMPY_GetGlobalParent.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetGlobalParent.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetValueName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetValueName.restype = c_char_p

ffi.lib.LLVMPY_SetValueName.argtypes = [ffi.LLVMValueRef, c_char_p]

ffi.lib.LLVMPY_TypeOf.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_TypeOf.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetLinkage.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetLinkage.restype = c_int

ffi.lib.LLVMPY_SetLinkage.argtypes = [ffi.LLVMValueRef, c_int]
