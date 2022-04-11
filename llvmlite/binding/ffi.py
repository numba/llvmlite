import contextlib
import ctypes
import importlib.resources
import os
import threading

from llvmlite.binding.common import _decode_string, _is_shutting_down
from llvmlite.utils import get_library_name


def _make_opaque_ref(name):
    newcls = type(name, (ctypes.Structure,), {})
    return ctypes.POINTER(newcls)


LLVMContextRef = _make_opaque_ref("LLVMContext")
LLVMModuleRef = _make_opaque_ref("LLVMModule")
LLVMValueRef = _make_opaque_ref("LLVMValue")
LLVMTypeRef = _make_opaque_ref("LLVMType")
LLVMExecutionEngineRef = _make_opaque_ref("LLVMExecutionEngine")
LLVMPassManagerBuilderRef = _make_opaque_ref("LLVMPassManagerBuilder")
LLVMPassManagerRef = _make_opaque_ref("LLVMPassManager")
LLVMTargetDataRef = _make_opaque_ref("LLVMTargetData")
LLVMTargetLibraryInfoRef = _make_opaque_ref("LLVMTargetLibraryInfo")
LLVMTargetRef = _make_opaque_ref("LLVMTarget")
LLVMTargetMachineRef = _make_opaque_ref("LLVMTargetMachine")
LLVMMemoryBufferRef = _make_opaque_ref("LLVMMemoryBuffer")
LLVMAttributeListIterator = _make_opaque_ref("LLVMAttributeListIterator")
LLVMAttributeSetIterator = _make_opaque_ref("LLVMAttributeSetIterator")
LLVMGlobalsIterator = _make_opaque_ref("LLVMGlobalsIterator")
LLVMFunctionsIterator = _make_opaque_ref("LLVMFunctionsIterator")
LLVMBlocksIterator = _make_opaque_ref("LLVMBlocksIterator")
LLVMArgumentsIterator = _make_opaque_ref("LLVMArgumentsIterator")
LLVMInstructionsIterator = _make_opaque_ref("LLVMInstructionsIterator")
LLVMOperandsIterator = _make_opaque_ref("LLVMOperandsIterator")
LLVMTypesIterator = _make_opaque_ref("LLVMTypesIterator")
LLVMObjectCacheRef = _make_opaque_ref("LLVMObjectCache")
LLVMObjectFileRef = _make_opaque_ref("LLVMObjectFile")
LLVMSectionIteratorRef = _make_opaque_ref("LLVMSectionIterator")


class _LLVMLock:
    """A Lock to guarantee thread-safety for the LLVM C-API.

    This class implements __enter__ and __exit__ for acquiring and releasing
    the lock as a context manager.

    Also, callbacks can be attached so that every time the lock is acquired
    and released the corresponding callbacks will be invoked.
    """
    def __init__(self):
        # The reentrant lock is needed for callbacks that re-enter
        # the Python interpreter.
        self._lock = threading.RLock()
        self._cblist = []

    def register(self, acq_fn, rel_fn):
        """Register callbacks that are invoked immediately after the lock is
        acquired (``acq_fn()``) and immediately before the lock is released
        (``rel_fn()``).
        """
        self._cblist.append((acq_fn, rel_fn))

    def unregister(self, acq_fn, rel_fn):
        """Remove the registered callbacks.
        """
        self._cblist.remove((acq_fn, rel_fn))

    def __enter__(self):
        self._lock.acquire()
        # Invoke all callbacks
        for acq_fn, rel_fn in self._cblist:
            acq_fn()

    def __exit__(self, *exc_details):
        # Invoke all callbacks
        for acq_fn, rel_fn in self._cblist:
            rel_fn()
        self._lock.release()


class _suppress_cleanup_errors:
    def __init__(self, context):
        self._context = context

    def __enter__(self):
        return self._context.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self._context.__exit__(exc_type, exc_value, traceback)
        except PermissionError:
            pass  # Resource dylibs can't be deleted on Windows.


class _lib_wrapper(object):
    """Wrap libllvmlite with a lock such that only one thread may access it at
    a time.

    This class duck-types a CDLL.
    """

    def __init__(self):
        self._lock = _LLVMLock()
        self._lib_handle = None

    def _load_lib(self):
        _lib_load_errors = []
        # llvmlite native code may exist in one of two places, with the first
        # taking priority:
        # 1) In a shared library available as a resource of the llvmlite
        #    package. This may involve unpacking the shared library from an
        #    archive.
        # 2) Linked directly into the main binary. Symbols may be resolved
        #    from the main binary by passing None as the argument to
        #    ctypes.CDLL.
        for lib_context in (
                _suppress_cleanup_errors(importlib.resources.path(
                    __name__.rpartition(".")[0], get_library_name())),
                contextlib.nullcontext(None)):
            try:
                with lib_context as lib_path:
                    if os.name == 'nt' and not lib_path:
                        # The Windows implementation of ctypes.CDLL does not
                        # support None as an argument.
                        continue
                    self._lib_handle = ctypes.CDLL(lib_path and str(lib_path))
                    # Check that we can look up expected symbols.
                    _ = self._lib_handle.LLVMPY_GetVersionInfo()
                    break
            except (OSError, AttributeError) as e:
                # OSError may be raised if the file cannot be opened, or is not
                # a shared library.
                # AttributeError is raised if LLVMPY_GetVersionInfo does not
                # exist.
                _lib_load_errors.append(e)
        else:
            # None of the expected locations contains a loadable version of
            # llvmlite. Raise OSError with the first error seen during the load
            # event as the cause of this exception.
            raise OSError("Could not find/load shared object file") \
                from _lib_load_errors[0]

    @property
    def _lib(self):
        # Not threadsafe.
        if not self._lib_handle:
            self._load_lib()
        return self._lib_handle

    def _resolve(self, lazy_wrapper):
        """Resolve a lazy wrapper, and store it in the symbol table."""
        with self._lock:
            wrapper = getattr(self, lazy_wrapper.symbol_name)
            if wrapper is lazy_wrapper:
                cfn = getattr(self._lib, lazy_wrapper.symbol_name)
                if hasattr(lazy_wrapper, 'argtypes'):
                    cfn.argtypes = lazy_wrapper.argtypes
                if hasattr(lazy_wrapper, 'restype'):
                    cfn.restype = lazy_wrapper.restype
                if getattr(lazy_wrapper, 'threadsafe', False):
                    wrapper = cfn
                else:
                    wrapper = _lib_fn_wrapper(self._lock, cfn)
                setattr(self, lazy_wrapper.symbol_name, wrapper)
            return wrapper

    def __getattr__(self, name):
        wrapper = _lazy_lib_fn_wrapper(name)
        setattr(self, name, wrapper)
        return wrapper

    @property
    def _name(self):
        """The name of the library passed in the CDLL constructor.

        For duck-typing a ctypes.CDLL
        """
        return self._lib._name

    @property
    def _handle(self):
        """The system handle used to access the library.

        For duck-typing a ctypes.CDLL
        """
        return self._lib._handle


class _lazy_lib_fn_wrapper(object):
    """A lazy wrapper for a ctypes.CFUNCTYPE that resolves on call."""

    def __init__(self, symbol_name):
        self.symbol_name = symbol_name

    def __call__(self, *args, **kwargs):
        return lib._resolve(self)(*args, **kwargs)


class _lib_fn_wrapper(object):
    """Wraps and duck-types a ctypes.CFUNCTYPE to provide
    automatic locking when the wrapped function is called.

    TODO: we can add methods to mark the function as threadsafe
          and remove the locking-step on call when marked.
    """
    __slots__ = ['_lock', '_cfn']

    def __init__(self, lock, cfn):
        self._lock = lock
        self._cfn = cfn

    @property
    def argtypes(self):
        return self._cfn.argtypes

    @argtypes.setter
    def argtypes(self, argtypes):
        self._cfn.argtypes = argtypes

    @property
    def restype(self):
        return self._cfn.restype

    @restype.setter
    def restype(self, restype):
        self._cfn.restype = restype

    def __call__(self, *args, **kwargs):
        with self._lock:
            return self._cfn(*args, **kwargs)


lib = _lib_wrapper()


def register_lock_callback(acq_fn, rel_fn):
    """Register callback functions for lock acquire and release.
    *acq_fn* and *rel_fn* are callables that take no arguments.
    """
    lib._lock.register(acq_fn, rel_fn)


def unregister_lock_callback(acq_fn, rel_fn):
    """Remove the registered callback functions for lock acquire and release.
    The arguments are the same as used in `register_lock_callback()`.
    """
    lib._lock.unregister(acq_fn, rel_fn)


class _DeadPointer(object):
    """
    Dummy class to make error messages more helpful.
    """


class OutputString(object):
    """
    Object for managing the char* output of LLVM APIs.
    """
    _as_parameter_ = _DeadPointer()

    @classmethod
    def from_return(cls, ptr):
        """Constructing from a pointer returned from the C-API.
        The pointer must be allocated with LLVMPY_CreateString.

        Note
        ----
        Because ctypes auto-converts *restype* of *c_char_p* into a python
        string, we must use *c_void_p* to obtain the raw pointer.
        """
        return cls(init=ctypes.cast(ptr, ctypes.c_char_p))

    def __init__(self, owned=True, init=None):
        self._ptr = init if init is not None else ctypes.c_char_p(None)
        self._as_parameter_ = ctypes.byref(self._ptr)
        self._owned = owned

    def close(self):
        if self._ptr is not None:
            if self._owned:
                lib.LLVMPY_DisposeString(self._ptr)
            self._ptr = None
            del self._as_parameter_

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self, _is_shutting_down=_is_shutting_down):
        # Avoid errors trying to rely on globals and modules at interpreter
        # shutdown.
        if not _is_shutting_down():
            if self.close is not None:
                self.close()

    def __str__(self):
        if self._ptr is None:
            return "<dead OutputString>"
        s = self._ptr.value
        assert s is not None
        return _decode_string(s)

    def __bool__(self):
        return bool(self._ptr)

    __nonzero__ = __bool__

    @property
    def bytes(self):
        """Get the raw bytes of content of the char pointer.
        """
        return self._ptr.value


def ret_string(ptr):
    """To wrap string return-value from C-API.
    """
    if ptr is not None:
        return str(OutputString.from_return(ptr))


def ret_bytes(ptr):
    """To wrap bytes return-value from C-API.
    """
    if ptr is not None:
        return OutputString.from_return(ptr).bytes


class ObjectRef(object):
    """
    A wrapper around a ctypes pointer to a LLVM object ("resource").
    """
    _closed = False
    _as_parameter_ = _DeadPointer()
    # Whether this object pointer is owned by another one.
    _owned = False

    def __init__(self, ptr):
        if ptr is None:
            raise ValueError("NULL pointer")
        self._ptr = ptr
        self._as_parameter_ = ptr
        self._capi = lib

    def close(self):
        """
        Close this object and do any required clean-up actions.
        """
        try:
            if not self._closed and not self._owned:
                self._dispose()
        finally:
            self.detach()

    def detach(self):
        """
        Detach the underlying LLVM resource without disposing of it.
        """
        if not self._closed:
            del self._as_parameter_
            self._closed = True
            self._ptr = None

    def _dispose(self):
        """
        Dispose of the underlying LLVM resource.  Should be overriden
        by subclasses.  Automatically called by close(), __del__() and
        __exit__() (unless the resource has been detached).
        """

    @property
    def closed(self):
        """
        Whether this object has been closed.  A closed object can't
        be used anymore.
        """
        return self._closed

    def __enter__(self):
        assert hasattr(self, "close")
        if self._closed:
            raise RuntimeError("%s instance already closed" % (self.__class__,))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self, _is_shutting_down=_is_shutting_down):
        if not _is_shutting_down():
            if self.close is not None:
                self.close()

    def __bool__(self):
        return bool(self._ptr)

    def __eq__(self, other):
        if not hasattr(other, "_ptr"):
            return False
        return ctypes.addressof(self._ptr[0]) == \
            ctypes.addressof(other._ptr[0])

    __nonzero__ = __bool__

    # XXX useful?
    def __hash__(self):
        return hash(ctypes.cast(self._ptr, ctypes.c_void_p).value)
