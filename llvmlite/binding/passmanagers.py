from __future__ import print_function, absolute_import
from ctypes import c_bool
from . import ffi


def create_module_pass_manager():
    return ModulePassManager(ffi.lib.LLVMPY_CreatePassManager())


def create_function_pass_manager(module):
    fpm = ffi.lib.LLVMPY_CreateFunctionPassManager(module)
    return FunctionPassManager(fpm)


class PassManager(ffi.ObjectRef):
    """PassManager
    """

    def close(self):
        ffi.lib.LLVMPY_DisposePassManager(self)


class ModulePassManager(PassManager):
    def run(self, module):
        return ffi.lib.LLVMPY_RunPassManager(self, module)


class FunctionPassManager(PassManager):
    def initialize(self):
        return ffi.lib.LLVMPY_InitializeFunctionPassManager(self)

    def finalize(self):
        return ffi.lib.LLVMPY_FinalizeFunctionPassManager(self)

    def run(self, function):
        return ffi.lib.LLVMPY_RunFunctionPassManager(self, function)


# ============================================================================
# FFI

ffi.lib.LLVMPY_CreatePassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_DisposePassManager.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_CreateFunctionPassManager.argtypes = [ffi.LLVMModuleRef]

ffi.lib.LLVMPY_RunFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                                  ffi.LLVMValueRef]
ffi.lib.LLVMPY_RunFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_InitializeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_InitializeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_FinalizeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_FinalizeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_RunFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                                  ffi.LLVMValueRef]
ffi.lib.LLVMPY_RunFunctionPassManager.restype = c_bool
