from __future__ import print_function, absolute_import
from ctypes import byref, POINTER, c_char_p, c_bool, c_uint, c_void_p
from . import ffi


def link_in_jit():
    ffi.lib.LLVMPY_LinkInJIT()


def link_in_mcjit():
    ffi.lib.LLVMPY_LinkInMCJIT()


def create_jit_compiler(module, opt=2):
    """Create an ExecutionEngine for a module
    """
    engine = ffi.LLVMExecutionEngineRef()
    with ffi.OutputString() as outerr:
        if ffi.lib.LLVMPY_CreateJITCompiler(byref(engine), module, opt,
                                            outerr):
            raise RuntimeError(str(outerr))

    print(engine.contents)
    return ExecutionEngine(engine)


class ExecutionEngine(ffi.ObjectRef):
    """An ExecutionEngine owns all Modules associated with it.
    Deleting the engine will remove all associated modules.
    It is an error to delete the associated mdoules.
    """

    def get_pointer_to_global(self, gv):
        ptr = ffi.lib.LLVMPY_GetPointerToGlobal(self, gv)
        if ptr is None:
            raise ValueError("Cannot find given global value")
        return ptr

    def add_global_mapping(self, gv, addr):
        ffi.lib.LLVMPY_AddGlobalMapping(self, gv, addr)

    def add_module(self, module):
        ffi.lib.LLVMPY_AddModule(self, module)

    def remove_module(self, module):
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_RemoveModule(self, module, outerr):
                raise RuntimeError(outerr)

    def close(self):
        ffi.lib.LLVMPY_DisposeExecutionEngine(self)


# ============================================================================
# FFI


ffi.lib.LLVMPY_CreateJITCompiler.argtypes = [
    POINTER(ffi.LLVMExecutionEngineRef),
    ffi.LLVMModuleRef,
    c_uint,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateJITCompiler.restype = c_bool

ffi.lib.LLVMPY_RemoveModule.argtypes = [
    ffi.LLVMExecutionEngineRef,
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_RemoveModule.restype = c_bool

ffi.lib.LLVMPY_AddModule.argtypes = [
    ffi.LLVMExecutionEngineRef,
    ffi.LLVMModuleRef
]

ffi.lib.LLVMPY_GetPointerToGlobal.argtypes = [ffi.LLVMExecutionEngineRef,
                                              ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetPointerToGlobal.restype = c_void_p

ffi.lib.LLVMPY_AddGlobalMapping.argtypes = [ffi.LLVMExecutionEngineRef,
                                            ffi.LLVMValueRef,
                                            c_void_p]

