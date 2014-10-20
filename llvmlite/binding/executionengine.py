from __future__ import print_function, absolute_import
from ctypes import byref, POINTER, c_char_p, c_bool, c_uint, c_void_p
from . import ffi, targets


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

    return ExecutionEngine(engine, module=module)


def create_mcjit_compiler(module, opt=2, relocmodel='default', emitdebug=False):
    """Create a MCJIT ExecutionEngine
    """
    if relocmodel not in ('default', 'static', 'pic', 'dynamicnopic'):
        raise ValueError("invalid relocation model %r" % (relocmodel,))
    engine = ffi.LLVMExecutionEngineRef()
    with ffi.OutputString() as outerr:
        if ffi.lib.LLVMPY_CreateMCJITCompilerCustom(
                byref(engine), module, opt,
                relocmodel.lower().encode('ascii'),
                int(bool(emitdebug)), outerr):
            raise RuntimeError(str(outerr))

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
        module.detach()
        ffi.ObjectRef.__init__(self, ptr)

    def get_pointer_to_global(self, gv):
        # XXX getPointerToGlobal is deprecated for MCJIT,
        # getGlobalValueAddress should be used instead.
        ptr = ffi.lib.LLVMPY_GetPointerToGlobal(self, gv)
        if ptr is None:
            raise ValueError("Cannot find given global value")
        return ptr

    get_pointer_to_function = get_pointer_to_global

    def add_global_mapping(self, gv, addr):
        ffi.lib.LLVMPY_AddGlobalMapping(self, gv, addr)

    def add_module(self, module):
        """
        Ownership of module is transferred to the execution engine
        """
        ffi.lib.LLVMPY_AddModule(self, module)
        self._modules.add(module)
        module.detach()

    def finalize_object(self):
        ffi.lib.LLVMPY_FinalizeObject(self)

    def remove_module(self, module):
        """
        Ownership of module is returned
        """
        self._modules.remove(module)
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_RemoveModule(self, module, outerr):
                raise RuntimeError(str(outerr))
        module.reattach()

    @property
    def target_data(self):
        td = ffi.lib.LLVMPY_GetExecutionEngineTargetData(self)
        ret = targets.TargetData(td)
        ret.detach()
        return ret

    def close(self):
        if not self._closed:
            # The modules will be cleaned up by the EE
            for mod in self._modules:
                mod.close_detached()
            ffi.lib.LLVMPY_DisposeExecutionEngine(self)
            ffi.ObjectRef.close(self)


# ============================================================================
# FFI


ffi.lib.LLVMPY_CreateJITCompiler.argtypes = [
    POINTER(ffi.LLVMExecutionEngineRef),
    ffi.LLVMModuleRef,
    c_uint,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateJITCompiler.restype = c_bool

ffi.lib.LLVMPY_CreateMCJITCompilerCustom.argtypes = [
    POINTER(ffi.LLVMExecutionEngineRef),
    ffi.LLVMModuleRef,
    c_uint,
    c_char_p,
    c_uint,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateMCJITCompilerCustom.restype = c_bool

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
