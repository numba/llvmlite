from __future__ import print_function, absolute_import
from ctypes import c_bool
from . import ffi


def create_module_pass_manager():
    return ModulePassManager()


def create_function_pass_manager(module):
    return FunctionPassManager(module)


class PassManager(ffi.ObjectRef):
    """PassManager
    """

    def _dispose(self):
        self._capi.LLVMPY_DisposePassManager(self)


class ModulePassManager(PassManager):

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_CreatePassManager()
        PassManager.__init__(self, ptr)

    def run(self, module):
        return ffi.lib.LLVMPY_RunPassManager(self, module)


class FunctionPassManager(PassManager):

    def __init__(self, module):
        ptr = ffi.lib.LLVMPY_CreateFunctionPassManager(module)
        self._module = module
        module._owned = True
        PassManager.__init__(self, ptr)

    def initialize(self):
        """
        Initialize the FunctionPassManager.  Returns True if it produced
        any changes (?).
        """
        return ffi.lib.LLVMPY_InitializeFunctionPassManager(self)

    def finalize(self):
        """
        Finalize the FunctionPassManager.  Returns True if it produced
        any changes (?).
        """
        return ffi.lib.LLVMPY_FinalizeFunctionPassManager(self)

    def run(self, function):
        return ffi.lib.LLVMPY_RunFunctionPassManager(self, function)


# ============================================================================
# FFI

ffi.lib.LLVMPY_CreatePassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_CreateFunctionPassManager.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_CreateFunctionPassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_DisposePassManager.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_RunPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                          ffi.LLVMModuleRef]
ffi.lib.LLVMPY_RunPassManager.restype = c_bool

ffi.lib.LLVMPY_InitializeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_InitializeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_FinalizeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_FinalizeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_RunFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                                  ffi.LLVMValueRef]
ffi.lib.LLVMPY_RunFunctionPassManager.restype = c_bool
