from ctypes import c_bool

from llvmlite.binding import ffi


def create_context():
    return ContextRef(ffi.lib.LLVMPY_ContextCreate(True))


def get_global_context():
    return GlobalContextRef(ffi.lib.LLVMPY_GetGlobalContext(True))


class ContextRef(ffi.ObjectRef):
    def __init__(self, context_ptr):
        super(ContextRef, self).__init__(context_ptr)

    def supports_typed_pointers(self):
        return ffi.lib.LLVMPY_SupportsTypedPointers(self)

    def _dispose(self):
        ffi.lib.LLVMPY_ContextDispose(self)


class GlobalContextRef(ContextRef):
    def _dispose(self):
        pass


ffi.lib.LLVMPY_GetGlobalContext.argtypes = [c_bool]
ffi.lib.LLVMPY_GetGlobalContext.restype = ffi.LLVMContextRef

ffi.lib.LLVMPY_ContextCreate.argtypes = [c_bool]
ffi.lib.LLVMPY_ContextCreate.restype = ffi.LLVMContextRef

ffi.lib.LLVMPY_SupportsTypedPointers.argtypes = [ffi.LLVMContextRef]
ffi.lib.LLVMPY_SupportsTypedPointers.restype = c_bool

ffi.lib.LLVMPY_ContextDispose.argtypes = [ffi.LLVMContextRef]
