from __future__ import print_function, absolute_import

from ctypes import (POINTER, c_char_p, c_bool, c_void_p,
                    c_int, c_uint64, c_size_t, CFUNCTYPE, string_at, cast,
                    py_object, Structure)
import warnings

from . import ffi, targets, object_file


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
    _object_cache = None

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
        """
        Return the address of the function named *name* as an integer.
        """
        ptr = ffi.lib.LLVMPY_GetFunctionAddress(self, name.encode("ascii"))
        if ptr is None:
            raise ValueError("Cannot find given function %s" % name)
        return ptr

    def get_global_value_address(self, name):
        """
        Return the address of the global value named *name* as an integer.
        """
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
        """
        Make sure all modules owned by the execution engine are fully processed
        and "usable" for execution.
        """
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

    def enable_jit_events(self):
        """
        Enable JIT events for profiling of generated code.
        Return value indicates whether connection to profiling tool
        was successful.
        """
        ret = ffi.lib.LLVMPY_EnableJITEvents(self)
        return ret

    def _find_module_ptr(self, module_ptr):
        """
        Find the ModuleRef corresponding to the given pointer.
        """
        ptr = cast(module_ptr, c_void_p).value
        for module in self._modules:
            if cast(module._ptr, c_void_p).value == ptr:
                return module
        return None

    def set_object_cache(self, notify_func=None, getbuffer_func=None):
        """
        Set the object cache "notifyObjectCompiled" and "getBuffer"
        callbacks to the given Python functions.
        """
        self._object_cache_notify = notify_func
        self._object_cache_getbuffer = getbuffer_func
        # Lifetime of the object cache is managed by us.
        self._object_cache = _ObjectCacheRef(self)
        # Note this doesn't keep a reference to self, to avoid reference
        # cycles.
        ffi.lib.LLVMPY_SetObjectCache(self, self._object_cache)

    def _raw_object_cache_notify(self, data):
        """
        Low-level notify hook.
        """
        if self._object_cache_notify is None:
            return
        module_ptr = data.contents.module_ptr
        buf_ptr = data.contents.buf_ptr
        buf_len = data.contents.buf_len
        buf = string_at(buf_ptr, buf_len)
        module = self._find_module_ptr(module_ptr)
        if module is None:
            # The LLVM EE should only give notifications for modules
            # known by us.
            raise RuntimeError("object compilation notification "
                               "for unknown module %s" % (module_ptr,))
        self._object_cache_notify(module, buf)

    def _raw_object_cache_getbuffer(self, data):
        """
        Low-level getbuffer hook.
        """
        if self._object_cache_getbuffer is None:
            return
        module_ptr = data.contents.module_ptr
        module = self._find_module_ptr(module_ptr)
        if module is None:
            # The LLVM EE should only give notifications for modules
            # known by us.
            raise RuntimeError("object compilation notification "
                               "for unknown module %s" % (module_ptr,))

        buf = self._object_cache_getbuffer(module)
        if buf is not None:
            # Create a copy, which will be freed by the caller
            data[0].buf_ptr = ffi.lib.LLVMPY_CreateByteString(buf, len(buf))
            data[0].buf_len = len(buf)

    def _dispose(self):
        # The modules will be cleaned up by the EE
        for mod in self._modules:
            mod.detach()
        if self._td is not None:
            self._td.detach()
        self._modules.clear()
        self._object_cache = None
        self._capi.LLVMPY_DisposeExecutionEngine(self)


class _ObjectCacheRef(ffi.ObjectRef):
    """
    Internal: an ObjectCache instance for use within an ExecutionEngine.
    """

    def __init__(self, obj):
        ptr = ffi.lib.LLVMPY_CreateObjectCache(_notify_c_hook,
                                               _getbuffer_c_hook,
                                               obj)
        ffi.ObjectRef.__init__(self, ptr)

    def _dispose(self):
        self._capi.LLVMPY_DisposeObjectCache(self)


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


class _ObjectCacheData(Structure):
    _fields_ = [
        ('module_ptr', ffi.LLVMModuleRef),
        ('buf_ptr', c_void_p),
        ('buf_len', c_size_t),
        ]


_ObjectCacheNotifyFunc = CFUNCTYPE(None, py_object,
                                   POINTER(_ObjectCacheData))
_ObjectCacheGetBufferFunc = CFUNCTYPE(None, py_object,
                                      POINTER(_ObjectCacheData))

# XXX The ctypes function wrappers are created at the top-level, otherwise
# there are issues when creating CFUNCTYPEs in child processes on CentOS 5 32 bits.
_notify_c_hook = _ObjectCacheNotifyFunc(ExecutionEngine._raw_object_cache_notify)
_getbuffer_c_hook = _ObjectCacheGetBufferFunc(ExecutionEngine._raw_object_cache_getbuffer)

ffi.lib.LLVMPY_CreateObjectCache.argtypes = [_ObjectCacheNotifyFunc,
                                             _ObjectCacheGetBufferFunc,
                                             py_object]
ffi.lib.LLVMPY_CreateObjectCache.restype = ffi.LLVMObjectCacheRef

ffi.lib.LLVMPY_DisposeObjectCache.argtypes = [ffi.LLVMObjectCacheRef]

ffi.lib.LLVMPY_SetObjectCache.argtypes = [ffi.LLVMExecutionEngineRef,
                                          ffi.LLVMObjectCacheRef]

ffi.lib.LLVMPY_CreateByteString.restype = c_void_p
ffi.lib.LLVMPY_CreateByteString.argtypes = [c_void_p, c_size_t]
