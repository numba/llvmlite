from __future__ import print_function, absolute_import
from ctypes import byref, POINTER, c_char_p, c_bool, c_uint, c_void_p
from . import ffi


def create_pass_manager_builder():
    return PassManagerBuilder(ffi.lib.LLVMPY_PassManagerBuilderCreate())


class PassManagerBuilder(ffi.ObjectRef):
    def _populate_module_pm(self, pm):
        ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManage(self, pm)

    def close(self):
        ffi.lib.LLVMPY_PassManagerBuilderDispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# ============================================================================
# FFI

ffi.lib.LLVMPY_PassManagerBuilderCreate.restype = ffi.LLVMPassManagerBuilderRef

ffi.lib.LLVMPY_PassManagerBuilderDispose.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManage = [
    ffi.LLVMPassManagerBuilderRef,
    ffi.LLVMPassManagerRef,
]
