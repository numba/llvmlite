from __future__ import print_function, absolute_import
from ctypes import POINTER, c_char_p, c_ulonglong
from . import ffi, parse_assembly


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
        if not self._closed:
            ffi.lib.LLVMPY_DisposeTargetData(self)
            ffi.ObjectRef.close(self)

    def abi_size(self, ty):
        from llvmlite.ir import Type, Module, GlobalVariable

        if isinstance(ty, Type):
            # We need to convert our type object to the LLVM's object
            m = Module()
            foo = GlobalVariable(m, ty, name="foo")
            with parse_assembly(str(m)) as mod:
                gv = mod.get_global_variable(foo.name)
                ty = gv.type

        return ffi.lib.LLVMPY_ABISizeOfType(self, ty)


# ============================================================================
# FFI

ffi.lib.LLVMPY_GetDefaultTargetTriple.argtypes = [POINTER(c_char_p)]

ffi.lib.LLVMPY_CreateTargetData.argtypes = [c_char_p]
ffi.lib.LLVMPY_CreateTargetData.restype = ffi.LLVMTargetDataRef

ffi.lib.LLVMPY_CopyStringRepOfTargetData.argtypes = [
    ffi.LLVMTargetDataRef,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_DisposeTargetData.argtypes = [
    ffi.LLVMTargetDataRef,
]

ffi.lib.LLVMPY_AddTargetData.argtypes = [ffi.LLVMTargetDataRef,
                                         ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_ABISizeOfType.argtypes = [ffi.LLVMTargetDataRef,
                                         ffi.LLVMTypeRef]
ffi.lib.LLVMPY_ABISizeOfType.restype = c_ulonglong

