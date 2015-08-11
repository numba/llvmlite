from __future__ import print_function, absolute_import

from ctypes import (byref, POINTER, c_char_p, c_bool, c_uint, c_void_p, c_int,
                    c_uint64)
import warnings

from . import ffi, targets


# Just check these weren't optimized out of the DLL.
ffi.lib.LLVMPY_LinkInMCJIT


def create_mcjit_compiler(module, target_machine):
    """
    Create a MCJIT ExecutionEngine from the given *module* and
    *target_machine*.
    """
    with ffi.OutputString() as outerr:
        engine = ffi.lib.LLVMPY_CreateMCJITCompiler(
                module, target_machine, outerr)
        if not engine:
            raise RuntimeError(str(outerr))

    target_machine._owned = True
    return ExecutionEngine(engine, module=module)


def check_jit_execution():
    """
    Check the system allows execution of in-memory JITted functions.
    An exception is raised otherwise.
    """
    errno = ffi.lib.LLVMPY_TryAllocateExecutableMemory()
    if errno != 0:
        raise OSError(errno,
                      "cannot allocate executable memory. "
                      "This may be due to security restrictions on your "
                      "system, such as SELinux or similar mechanisms."
                      )


class ExecutionEngine(ffi.ObjectRef):
    """An ExecutionEngine owns all Modules associated with it.
    Deleting the engine will remove all associated modules.
    It is an error to delete the associated modules.
    """

    def __init__(self, ptr, module):
        """
        Module ownership is transferred to the EE
        """
        self._modules = set([module])
        self._td = None
        module._owned = True
        ffi.ObjectRef.__init__(self, ptr)

    def get_pointer_to_function(self, gv):
        warnings.warn(".get_pointer_to_function() is deprecated.  Use "
                      ".get_function_address() instead.", DeprecationWarning)
        ptr = ffi.lib.LLVMPY_GetPointerToGlobal(self, gv)
        if ptr is None:
            raise ValueError("Cannot find given global value %r" % (gv.name))
        return ptr

    def get_function_address(self, name):
        ptr = ffi.lib.LLVMPY_GetFunctionAddress(self, name.encode("ascii"))
        if ptr is None:
            raise ValueError("Cannot find given function %s" % name)
        return ptr

    def get_global_value_address(self, name):
        ptr = ffi.lib.LLVMPY_GetGlobalValueAddress(self, name.encode("ascii"))
        if ptr is None:
            raise ValueError("Cannot find given global value %s" % name)
        return ptr

    def add_global_mapping(self, gv, addr):
        # XXX unused?
        ffi.lib.LLVMPY_AddGlobalMapping(self, gv, addr)

    def add_module(self, module):
        """
        Ownership of module is transferred to the execution engine
        """
        if module in self._modules:
            raise KeyError("module already added to this engine")
        ffi.lib.LLVMPY_AddModule(self, module)
        module._owned = True
        self._modules.add(module)

    def finalize_object(self):
        ffi.lib.LLVMPY_FinalizeObject(self)

    def remove_module(self, module):
        """
        Ownership of module is returned
        """
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_RemoveModule(self, module, outerr):
                raise RuntimeError(str(outerr))
        self._modules.remove(module)
        module._owned = False

    @property
    def target_data(self):
        """
        The TargetData for this execution engine.
        """
        if self._td is not None:
            return self._td
        ptr = ffi.lib.LLVMPY_GetExecutionEngineTargetData(self)
        self._td = targets.TargetData(ptr)
        self._td._owned = True
        return self._td

    def _dispose(self):
        # The modules will be cleaned up by the EE
        for mod in self._modules:
            mod.detach()
        if self._td is not None:
            self._td.detach()
        self._modules.clear()
        self._capi.LLVMPY_DisposeExecutionEngine(self)


# ============================================================================
# FFI


ffi.lib.LLVMPY_CreateMCJITCompiler.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMTargetMachineRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateMCJITCompiler.restype = ffi.LLVMExecutionEngineRef

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

ffi.lib.LLVMPY_FinalizeObject.argtypes = [ffi.LLVMExecutionEngineRef]

ffi.lib.LLVMPY_GetExecutionEngineTargetData.argtypes = [
    ffi.LLVMExecutionEngineRef
]
ffi.lib.LLVMPY_GetExecutionEngineTargetData.restype = ffi.LLVMTargetDataRef

ffi.lib.LLVMPY_TryAllocateExecutableMemory.argtypes = []
ffi.lib.LLVMPY_TryAllocateExecutableMemory.restype = c_int

ffi.lib.LLVMPY_GetFunctionAddress.argtypes = [
    ffi.LLVMExecutionEngineRef,
    c_char_p
]
ffi.lib.LLVMPY_GetFunctionAddress.restype = c_uint64

ffi.lib.LLVMPY_GetGlobalValueAddress.argtypes = [
    ffi.LLVMExecutionEngineRef,
    c_char_p
]
ffi.lib.LLVMPY_GetGlobalValueAddress.restype = c_uint64
