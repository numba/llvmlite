from ctypes import c_int, c_bool, c_void_p
import enum

from llvmlite.binding import ffi

class TypeKind(enum.IntEnum):
    # The LLVMTypeKind enum from llvm-c/Core.h

    void = 0
    half = 1
    float = 2
    double = 3
    x86_fp80 = 4
    fp128 = 5
    ppc_fp128 = 6
    label = 7
    integer = 8
    function = 9
    struct = 10
    array = 11
    pointer = 12
    vector = 13
    metadata = 14
    x86_mmx = 15
    token = 16
    scalable_vector = 17
    bfloat = 18
    x86_amx = 19


class TypeRef(ffi.ObjectRef):
    """A weak reference to a LLVM type
    """
    @property
    def name(self):
        """
        Get type name
        """
        return ffi.ret_string(ffi.lib.LLVMPY_GetTypeName(self))

    @property
    def is_pointer(self):
        """
        Returns true is the type is a pointer type.
        """
        return ffi.lib.LLVMPY_TypeIsPointer(self)

    @property
    def elements(self):
        """
        Returns iterator over enclosing types
        """
        return  _TypeListIterator(ffi.lib.LLVMPY_ElementIter(self))

    @property
    def element_type(self):
        """
        Returns the pointed-to type. When the type is not a pointer,
        raises exception.
        """
        if not self.is_pointer:
            raise ValueError("Type {} is not a pointer".format(self))
        return TypeRef(ffi.lib.LLVMPY_GetElementType(self))

    @property
    def type_kind(self):
        """
        Returns the LLVMTypeKind enumeration of this type.
        """
        return TypeKind(ffi.lib.LLVMPY_GetTypeKind(self))

    def __str__(self):
        return ffi.ret_string(ffi.lib.LLVMPY_PrintType(self))


class _TypeIterator(ffi.ObjectRef):

    def __next__(self):
        vp = self._next()
        if vp:
            return TypeRef(vp)
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _TypeListIterator(_TypeIterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeElementIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_ElementIterNext(self)


# FFI

ffi.lib.LLVMPY_PrintType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_PrintType.restype = c_void_p

ffi.lib.LLVMPY_GetElementType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetElementType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_TypeIsPointer.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsPointer.restype = c_bool

ffi.lib.LLVMPY_GetTypeKind.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeKind.restype = c_int

ffi.lib.LLVMPY_ElementIter.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_ElementIter.restype = ffi.LLVMElementIterator

ffi.lib.LLVMPY_ElementIterNext.argtypes = [ffi.LLVMElementIterator]
ffi.lib.LLVMPY_ElementIterNext.restype = ffi.LLVMTypeRef


ffi.lib.LLVMPY_DisposeElementIter.argtypes = [ffi.LLVMElementIterator]
