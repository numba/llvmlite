import ctypes
import os

from .common import _decode_string, _is_shutting_down
from ..utils import get_library_name
from ..six import PY2


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
LLVMGlobalsIterator = _make_opaque_ref("LLVMGlobalsIterator")
LLVMFunctionsIterator = _make_opaque_ref("LLVMFunctionsIterator")
LLVMObjectCacheRef = _make_opaque_ref("LLVMObjectCache")


_lib_dir = os.path.dirname(__file__)

if os.name == 'nt':
    # Append DLL directory to PATH, to allow loading of bundled CRT libraries
    # (Windows uses PATH for DLL loading, see http://msdn.microsoft.com/en-us/library/7d83bc18.aspx).
    os.environ['PATH'] += ';' + _lib_dir

_lib_name = get_library_name()
try:
    lib = ctypes.CDLL(os.path.join(_lib_dir, _lib_name))
except OSError as e:
    # Allow finding the llvmlite DLL in the current directory, for ease
    # of bundling with frozen applications.
    try:
        lib = ctypes.CDLL(_lib_name)
    except OSError:
        if PY2:
            raise e
        raise


class _DeadPointer(object):
    """
    Dummy class to make error messages more helpful.
    """


class OutputString(object):
    """
    Object for managing the char* output of LLVM APIs.
    """
    _as_parameter_ = _DeadPointer()

    def __init__(self, owned=True):
        self._ptr = ctypes.c_char_p(None)
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

    def __del__(self):
        self.close()

    def __bool__(self):
        return bool(self._ptr)

    __nonzero__ = __bool__

    # XXX useful?
    def __hash__(self):
        return hash(ctypes.cast(self._ptr, ctypes.c_void_p).value)

