from ctypes import POINTER, c_char_p, c_int

from . import ffi
from .common import _decode_string, _encode_string
import itertools

# Linkage Enum
_linkage_ct = itertools.count()
_linkage_get = lambda: next(_linkage_ct)

LINKAGE = {
    'external': _linkage_get(),
    'available_externally': _linkage_get(),
    'linkonce_any': _linkage_get(),
    'linkonce_odr': _linkage_get(),
    'linkonce_odr_autohide': _linkage_get(),
    'weak_any': _linkage_get(),
    'weak_odr': _linkage_get(),
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


# Attribute Enum

_attribute_ct = itertools.count()
_attribute_get = lambda: 1 << next(_attribute_ct)

ATTRIBUTE = {
    'zext': _attribute_get(),
    'sext': _attribute_get(),
    'noreturn': _attribute_get(),
    'inreg': _attribute_get(),
    'structret': _attribute_get(),
    'nounwind': _attribute_get(),
    'noalias': _attribute_get(),
    'byval': _attribute_get(),
    'nest': _attribute_get(),
    'readnone': _attribute_get(),
    'readonly': _attribute_get(),
    'noinline': _attribute_get(),
    'alwaysinline': _attribute_get(),
    'optimizeforsize': _attribute_get(),
    'stackprotect': _attribute_get(),
    'stackprotectreq': _attribute_get(),  # 1 << 15

    '_reserved0': _attribute_get(),
    '_reserved1': _attribute_get(),
    '_reserved2': _attribute_get(),
    '_reserved3': _attribute_get(),
    '_reserved4': _attribute_get(),

    'nocapture': _attribute_get(),
    'noredzone': _attribute_get(),
    'noimplicitfloat': _attribute_get(),
    'naked': _attribute_get(),
    'inlinehint': _attribute_get(),  # 1 << 25

    '_reserved5': _attribute_get(),
    '_reserved6': _attribute_get(),
    '_reserved7': _attribute_get(),

    'returnstwice': _attribute_get(), # 1 << 29
    'uwtable': _attribute_get(),
    'nonlazybind': _attribute_get(),
}


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
        ffi.lib.LLVMPY_SetValueName(self, _encode_string(val))

    @property
    def linkage(self):
        return _REVLINKAGE[ffi.lib.LLVMPY_GetLinkage(self)]

    @linkage.setter
    def linkage(self, value):
        ffi.lib.LLVMPY_SetLinkage(self, LINKAGE[value])

    def add_function_attribute(self, attr):
        """Only works on function value"""
        ffi.lib.LLVMPY_AddFunctionAttr(self, ATTRIBUTE[attr])


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

ffi.lib.LLVMPY_AddFunctionAttr.argtypes = [ffi.LLVMValueRef, c_int]
