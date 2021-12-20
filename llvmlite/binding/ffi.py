import ctypes
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


class _lib_wrapper(object):
    """Wrap libllvmlite with a lock such that only one thread may access it at
    a time.

    This class duck-types a CDLL.
    """
    __slots__ = ['_lib', '_fntab', '_lock']

    def __init__(self, lib):
        self._lib = lib
        self._fntab = {}
        self._lock = _LLVMLock()

    def __getattr__(self, name):
        try:
            return self._fntab[name]
        except KeyError:
            # Lazily wraps new functions as they are requested
            cfn = getattr(self._lib, name)
            wrapped = _lib_fn_wrapper(self._lock, cfn)
            self._fntab[name] = wrapped
            return wrapped

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


_lib_dir = os.path.dirname(__file__)

if os.name == 'nt':
    # Append DLL directory to PATH, to allow loading of bundled CRT libraries
    # (Windows uses PATH for DLL loading, see http://msdn.microsoft.com/en-us/library/7d83bc18.aspx).  # noqa E501
    os.environ['PATH'] += ';' + _lib_dir


_lib_name = get_library_name()


# Possible CDLL loading paths
_lib_paths = [
    os.path.join(_lib_dir, _lib_name),  # Absolute
    _lib_name,  # In PATH
    os.path.join('.', _lib_name),  # Current directory
]

# If pkg_resources is available, try to use it to load the shared object.
# This allows direct import from egg files.
try:
    from pkg_resources import resource_filename
except ImportError:
    pass
else:
    _lib_paths.append(resource_filename(__name__, _lib_name))


# Try to load from all of the different paths
errors = []
for _lib_path in _lib_paths:
    try:
        lib = ctypes.CDLL(_lib_path)
    except OSError as e:
        errors.append(e)
        continue
    else:
        break
else:
    msg = ("Could not load shared object file: {}\n".format(_lib_name) +
           "Errors were: {}".format(errors))
    raise OSError(msg)


lib = _lib_wrapper(lib)


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
