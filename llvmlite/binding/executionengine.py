from __future__ import print_function, absolute_import
from ctypes import byref, POINTER, c_char_p, c_bool, c_uint, c_void_p
from . import ffi, targets


# Just check these weren't optimized out of the DLL.
ffi.lib.LLVMPY_LinkInJIT
ffi.lib.LLVMPY_LinkInMCJIT


def create_jit_compiler(module, opt=2):
    """Create an ExecutionEngine for a module
    """
    engine = ffi.LLVMExecutionEngineRef()
    with ffi.OutputString() as outerr:
        if ffi.lib.LLVMPY_CreateJITCompiler(byref(engine), module, opt,
                                            outerr):
            raise RuntimeError(str(outerr))

    return ExecutionEngine(engine, module=module)



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


def create_jit_compiler_with_tm(module, target_machine):
    """
    Create a JIT ExecutionEngine from the given *module* and
    *target_machine*.
    """
    with ffi.OutputString() as outerr:
        engine = ffi.lib.LLVMPY_CreateJITCompilerWithTM(
            module, target_machine, outerr)
        if not engine:
            raise RuntimeError(str(outerr))

    target_machine._owned = True
    return ExecutionEngine(engine, module=module)


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

    def get_pointer_to_global(self, gv):
        # XXX getPointerToGlobal is deprecated for MCJIT,
        # getGlobalValueAddress should be used instead.
        ptr = ffi.lib.LLVMPY_GetPointerToGlobal(self, gv)
        if ptr is None:
            raise ValueError("Cannot find given global value %r" % (gv.name))
        return ptr

    get_pointer_to_function = get_pointer_to_global

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


ffi.lib.LLVMPY_CreateJITCompiler.argtypes = [
    POINTER(ffi.LLVMExecutionEngineRef),
    ffi.LLVMModuleRef,
    c_uint,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateJITCompiler.restype = c_bool

ffi.lib.LLVMPY_CreateJITCompilerWithTM.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMTargetMachineRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateJITCompilerWithTM.restype = ffi.LLVMExecutionEngineRef

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
