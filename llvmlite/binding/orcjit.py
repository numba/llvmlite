from ctypes import POINTER, c_bool, c_char_p, c_void_p, c_uint64, string_at

from llvmlite.binding import ffi, targets
from llvmlite.binding.common import _encode_string
from llvmlite.binding.executionengine import _ObjectCacheRef


class LLJIT(ffi.ObjectRef):
    def __init__(self, ptr):
        self._td = None
        self._resource_trackers = {}
        ffi.ObjectRef.__init__(self, ptr)

    def add_ir_module(self, m):
        if m in self._resource_trackers:
            raise KeyError("module already added to this engine")
        rt = ffi.lib.LLVMPY_AddIRModule(self, m)
        m._owned = True
        self._resource_trackers[m] = rt

    def remove_ir_module(self, m):
        if m not in self._resource_trackers:
            raise KeyError('Module not added to this LLJIT instance')
        rt = self._resource_trackers.pop(m)
        ffi.lib.LLVMPY_RemoveIRModule(rt)

    def lookup(self, fn):
        with ffi.OutputString() as outerr:
            ptr = ffi.lib.LLVMPY_LLJITLookup(self, fn.encode("ascii"), outerr)
            if not ptr:
                raise RuntimeError(str(outerr))

        return ptr

    @property
    def target_data(self):
        """
        The TargetData for this LLJIT instance.
        """
        if self._td is not None:
            return self._td
        ptr = ffi.lib.LLVMPY_LLJITGetDataLayout(self)
        self._td = targets.TargetData(ptr)
        self._td._owned = True
        return self._td

    def run_static_constructors(self):
        """
        Run static constructors which initialize module-level static objects.
        """
        ffi.lib.LLVMPY_LLJITRunInitializers(self)

    def run_static_destructors(self):
        """
        Run static destructors which perform module-level cleanup of static
        resources.
        """
        ffi.lib.LLVMPY_LLJITRunDeinitializers(self)

    def add_object_file(self, obj_file):
        """
        Add object file to this LLJIT instance. object_file can be instance of
        :class:ObjectFile or a string representing file system path.
        """
        if isinstance(obj_file, str):
            obj_file = object_file.ObjectFileRef.from_path(obj_file)

        with ffi.OutputString() as outerr:
            error = ffi.lib.LLVMPY_LLJITAddObjectFile(self, obj_file, outerr)
            if error:
                raise RuntimeError(str(outerr))

    def define_symbol(self, name, address):
        """
        Register the *address* of global symbol *name*.  This will make
        it usable (e.g. callable) from LLVM-compiled functions.
        """
        ffi.lib.LLVMPY_LLJITDefineSymbol(self, _encode_string(name),
                                         c_void_p(address))

    def add_current_process_search(self):
        """
        Enable searching for global symbols in the current process when
        linking.
        """
        ffi.lib.LLVMPY_LLJITAddCurrentProcessSearch(self)

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
        # The modules will be cleaned up by the LLJIT, but we need to release
        # the resource trackers.
        for mod, rt in self._resource_trackers.items():
            ffi.lib.LLVMPY_ReleaseResourceTracker(rt)
            mod.detach()
        if self._td is not None:
            self._td.detach()
        self._resource_trackers.clear()
        self._capi.LLVMPY_LLJITDispose(self)


def create_lljit_compiler(target_machine=None):
    """
    Create an LLJIT instance
    """
    with ffi.OutputString() as outerr:
        lljit = ffi.lib.LLVMPY_CreateLLJITCompiler(target_machine, outerr)
        if not lljit:
            raise RuntimeError(str(outerr))

    return LLJIT(lljit)


ffi.lib.LLVMPY_AddIRModule.argtypes = [
    ffi.LLVMOrcLLJITRef,
    ffi.LLVMModuleRef,
]


ffi.lib.LLVMPY_LLJITLookup.argtypes = [
    ffi.LLVMOrcLLJITRef,
    c_char_p,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_LLJITLookup.restype = c_uint64

ffi.lib.LLVMPY_LLJITGetDataLayout.argtypes = [
    ffi.LLVMOrcLLJITRef,
]
ffi.lib.LLVMPY_LLJITGetDataLayout.restype = ffi.LLVMTargetDataRef

ffi.lib.LLVMPY_CreateLLJITCompiler.argtypes = [
    ffi.LLVMTargetMachineRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_CreateLLJITCompiler.restype = ffi.LLVMOrcLLJITRef

ffi.lib.LLVMPY_LLJITDispose.argtypes = [
    ffi.LLVMOrcLLJITRef,
]

ffi.lib.LLVMPY_LLJITRunInitializers.argtypes = [
    ffi.LLVMOrcLLJITRef,
]

ffi.lib.LLVMPY_LLJITRunDeinitializers.argtypes = [
    ffi.LLVMOrcLLJITRef,
]


ffi.lib.LLVMPY_LLJITDefineSymbol.argtypes = [
    ffi.LLVMOrcLLJITRef,
    c_char_p,
    c_void_p,
]

ffi.lib.LLVMPY_LLJITAddCurrentProcessSearch.argtypes = [
    ffi.LLVMOrcLLJITRef,
]

ffi.lib.LLVMPY_AddIRModule.argtypes = [
    ffi.LLVMOrcLLJITRef,
    ffi.LLVMModuleRef,
]
ffi.lib.LLVMPY_AddIRModule.restype = ffi.LLVMOrcResourceTrackerRef


ffi.lib.LLVMPY_ReleaseResourceTracker.argtypes = [
    ffi.LLVMOrcResourceTrackerRef,
]

ffi.lib.LLVMPY_LLJITAddObjectFile.argtypes = [
    ffi.LLVMOrcLLJITRef,
    ffi.LLVMObjectFileRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_LLJITAddObjectFile.restype = c_bool
