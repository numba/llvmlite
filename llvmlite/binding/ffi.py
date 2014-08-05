import ctypes


def _make_opaque_ref(name):
    newcls = type(name, (ctypes.Structure,), {})
    return ctypes.POINTER(newcls)


LLVMContextRef = _make_opaque_ref("LLVMContext")
LLVMModuleRef = _make_opaque_ref("LLVMModule")
LLVMValueRef = _make_opaque_ref("LLVMValue")
LLVMExecutionEngineRef = _make_opaque_ref("LLVMExecutionEngine")
LLVMPassManagerBuilderRef = _make_opaque_ref("LLVMPassManagerBuilder")
LLVMPassManagerRef = _make_opaque_ref("LLVMPassManager")

lib = ctypes.CDLL('ffi/libllvmlite.dylib')


class OutputString(object):
    """Object for managing output string memory
    """

    def __init__(self):
        self.pointer = ctypes.c_char_p(None)
        self._as_parameter_ = ctypes.byref(self.pointer)

    def close(self):
        lib.LLVMPY_DisposeString(self.pointer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        assert self.pointer.value is not None
        return self.pointer.value.decode('utf8')

    def __bool__(self):
        return bool(self.pointer)


class ObjectRef(object):
    """Weak reference to LLVM objects
    """

    def __init__(self, ptr):
        self._ptr = ptr
        self._as_parameter_ = ptr

