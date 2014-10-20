import ctypes
import os
import sys


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
LLVMTargetLibraryInfoRef = _make_opaque_ref(("LLVMTargetLibraryInfo"))

ffi_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ffi')

if sys.platform == 'darwin':
    lib = ctypes.CDLL(os.path.join(ffi_dir, 'libllvmlite.dylib'))
else:
    assert os.name == 'posix'
    lib = ctypes.CDLL(os.path.join(ffi_dir, 'libllvmlite.so'))


class OutputString(object):
    """Object for managing output string memory
    """

    def __init__(self, owned=True):
        self.pointer = ctypes.c_char_p(None)
        self._as_parameter_ = ctypes.byref(self.pointer)
        self._owned = owned

    def close(self):
        if self.pointer is not None:
            if self._owned:
                lib.LLVMPY_DisposeString(self.pointer)
            self.pointer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        if self.pointer is None:
            return "<dead OutputString>"
        s = self.pointer.value
        assert s is not None
        return s.decode('utf8')

    def __bool__(self):
        return bool(self.pointer)

    __nonzero__ = __bool__


class _DeadPointer(object):
    """
    Dummy class to make error messages more helpful.
    """


class ObjectRef(object):
    """Weak reference to LLVM objects
    """
    _closed = False
    _as_parameter_ = _DeadPointer()

    def __init__(self, ptr):
        if ptr is None:
            raise ValueError("NULL pointer")
        self._ptr = ptr
        self._as_parameter_ = ptr

    def close(self):
        del self._as_parameter_
        self._closed = True
        self._ptr = None

    def __enter__(self):
        assert hasattr(self, "close")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __bool__(self):
        return bool(self._ptr)

    def __eq__(self, other):
        return (type(self) is type(other) and self._ptr is not None
                and self._ptr == other._ptr)

    def __ne__(self, other):
        return not (self == other)

    __nonzero__ = __bool__
