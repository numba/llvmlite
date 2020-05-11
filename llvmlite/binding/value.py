from ctypes import POINTER, c_char_p, c_int, c_size_t, c_uint, c_bool, c_void_p
import enum

from llvmlite.binding import ffi
from llvmlite.binding.common import _decode_string, _encode_string


class Linkage(enum.IntEnum):
    # The LLVMLinkage enum from llvm-c/Core.h

    external = 0
    available_externally = 1
    linkonce_any = 2
    linkonce_odr = 3
    linkonce_odr_autohide = 4
    weak_any = 5
    weak_odr = 6
    appending = 7
    internal = 8
    private = 9
    dllimport = 10
    dllexport = 11
    external_weak = 12
    ghost = 13
    common = 14
    linker_private = 15
    linker_private_weak = 16


class Visibility(enum.IntEnum):
    # The LLVMVisibility enum from llvm-c/Core.h

    default = 0
    hidden = 1
    protected = 2


class StorageClass(enum.IntEnum):
    # The LLVMDLLStorageClass enum from llvm-c/Core.h

    default = 0
    dllimport = 1
    dllexport = 2


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
    def element_type(self):
        """
        Returns the pointed-to type. When the type is not a pointer,
        raises exception.
        """
        if not self.is_pointer:
            raise ValueError("Type {} is not a pointer".format(self))
        return TypeRef(ffi.lib.LLVMPY_GetElementType(self))

    def __str__(self):
        return ffi.ret_string(ffi.lib.LLVMPY_PrintType(self))


class ValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value.
    """

    def __init__(self, ptr, kind, parents):
        self._kind = kind
        self._parents = parents
        ffi.ObjectRef.__init__(self, ptr)

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)

    @property
    def module(self):
        """
        The module this function or global variable value was obtained from.
        """
        return self._parents.get('module')

    @property
    def function(self):
        """
        The function this argument or basic block value was obtained from.
        """
        return self._parents.get('function')

    @property
    def block(self):
        """
        The block this instruction value was obtained from.
        """
        return self._parents.get('block')

    @property
    def instruction(self):
        """
        The instruction this operand value was obtained from.
        """
        return self._parents.get('instruction')

    @property
    def is_global(self):
        return self._kind == 'global'

    @property
    def is_function(self):
        return self._kind == 'function'

    @property
    def is_block(self):
        return self._kind == 'block'

    @property
    def is_argument(self):
        return self._kind == 'argument'

    @property
    def is_instruction(self):
        return self._kind == 'instruction'

    @property
    def is_operand(self):
        return self._kind == 'operand'

    @property
    def name(self):
        return _decode_string(ffi.lib.LLVMPY_GetValueName(self))

    @name.setter
    def name(self, val):
        ffi.lib.LLVMPY_SetValueName(self, _encode_string(val))

    @property
    def linkage(self):
        return Linkage(ffi.lib.LLVMPY_GetLinkage(self))

    @linkage.setter
    def linkage(self, value):
        if not isinstance(value, Linkage):
            value = Linkage[value]
        ffi.lib.LLVMPY_SetLinkage(self, value)

    @property
    def visibility(self):
        return Visibility(ffi.lib.LLVMPY_GetVisibility(self))

    @visibility.setter
    def visibility(self, value):
        if not isinstance(value, Visibility):
            value = Visibility[value]
        ffi.lib.LLVMPY_SetVisibility(self, value)

    @property
    def storage_class(self):
        return StorageClass(ffi.lib.LLVMPY_GetDLLStorageClass(self))

    @storage_class.setter
    def storage_class(self, value):
        if not isinstance(value, StorageClass):
            value = StorageClass[value]
        ffi.lib.LLVMPY_SetDLLStorageClass(self, value)

    def add_function_attribute(self, attr):
        """Only works on function value

        Parameters
        -----------
        attr : str
            attribute name
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        attrname = str(attr)
        attrval = ffi.lib.LLVMPY_GetEnumAttributeKindForName(
            _encode_string(attrname), len(attrname))
        if attrval == 0:
            raise ValueError('no such attribute {!r}'.format(attrname))
        ffi.lib.LLVMPY_AddFunctionAttr(self, attrval)

    @property
    def type(self):
        """
        This value's LLVM type.
        """
        # XXX what does this return?
        return TypeRef(ffi.lib.LLVMPY_TypeOf(self))

    @property
    def is_declaration(self):
        """
        Whether this value (presumably global) is defined in the current
        module.
        """
        if not (self.is_global or self.is_function):
            raise ValueError('expected global or function value, got %s'
                             % (self._kind,))
        return ffi.lib.LLVMPY_IsDeclaration(self)

    @property
    def attributes(self):
        """
        Return an iterator over this value's attributes.
        The iterator will yield a string for each attribute.
        """
        itr = iter(())
        if self.is_function:
            it = ffi.lib.LLVMPY_FunctionAttributesIter(self)
            itr = _AttributeListIterator(it)
        elif self.is_instruction:
            if self.opcode == 'call':
                it = ffi.lib.LLVMPY_CallInstAttributesIter(self)
                itr = _AttributeListIterator(it)
            elif self.opcode == 'invoke':
                it = ffi.lib.LLVMPY_InvokeInstAttributesIter(self)
                itr = _AttributeListIterator(it)
        elif self.is_global:
            it = ffi.lib.LLVMPY_GlobalAttributesIter(self)
            itr = _AttributeSetIterator(it)
        elif self.is_argument:
            it = ffi.lib.LLVMPY_ArgumentAttributesIter(self)
            itr = _AttributeSetIterator(it)
        return itr

    @property
    def blocks(self):
        """
        Return an iterator over this function's blocks.
        The iterator will yield a ValueRef for each block.
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_FunctionBlocksIter(self)
        parents = self._parents.copy()
        parents.update(function=self)
        return _BlocksIterator(it, parents)

    @property
    def arguments(self):
        """
        Return an iterator over this function's arguments.
        The iterator will yield a ValueRef for each argument.
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_FunctionArgumentsIter(self)
        parents = self._parents.copy()
        parents.update(function=self)
        return _ArgumentsIterator(it, parents)

    @property
    def instructions(self):
        """
        Return an iterator over this block's instructions.
        The iterator will yield a ValueRef for each instruction.
        """
        if not self.is_block:
            raise ValueError('expected block value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_BlockInstructionsIter(self)
        parents = self._parents.copy()
        parents.update(block=self)
        return _InstructionsIterator(it, parents)

    @property
    def operands(self):
        """
        Return an iterator over this instruction's operands.
        The iterator will yield a ValueRef for each operand.
        """
        if not self.is_instruction:
            raise ValueError('expected instruction value, got %s'
                             % (self._kind,))
        it = ffi.lib.LLVMPY_InstructionOperandsIter(self)
        parents = self._parents.copy()
        parents.update(instruction=self)
        return _OperandsIterator(it, parents)

    @property
    def opcode(self):
        if not self.is_instruction:
            raise ValueError('expected instruction value, got %s'
                             % (self._kind,))
        return ffi.ret_string(ffi.lib.LLVMPY_GetOpcodeName(self))


class _ValueIterator(ffi.ObjectRef):

    kind = None  # derived classes must specify the Value kind value
    # as class attribute

    def __init__(self, ptr, parents):
        ffi.ObjectRef.__init__(self, ptr)
        # Keep parent objects (module, function, etc) alive
        self._parents = parents
        if self.kind is None:
            raise NotImplementedError('%s must specify kind attribute'
                                      % (type(self).__name__,))

    def __next__(self):
        vp = self._next()
        if vp:
            return ValueRef(vp, self.kind, self._parents)
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _AttributeIterator(ffi.ObjectRef):

    def __next__(self):
        vp = self._next()
        if vp:
            return vp
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _AttributeListIterator(_AttributeIterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeAttributeListIter(self)

    def _next(self):
        return ffi.ret_bytes(ffi.lib.LLVMPY_AttributeListIterNext(self))


class _AttributeSetIterator(_AttributeIterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeAttributeSetIter(self)

    def _next(self):
        return ffi.ret_bytes(ffi.lib.LLVMPY_AttributeSetIterNext(self))


class _BlocksIterator(_ValueIterator):

    kind = 'block'

    def _dispose(self):
        self._capi.LLVMPY_DisposeBlocksIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_BlocksIterNext(self)


class _ArgumentsIterator(_ValueIterator):

    kind = 'argument'

    def _dispose(self):
        self._capi.LLVMPY_DisposeArgumentsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_ArgumentsIterNext(self)


class _InstructionsIterator(_ValueIterator):

    kind = 'instruction'

    def _dispose(self):
        self._capi.LLVMPY_DisposeInstructionsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_InstructionsIterNext(self)


class _OperandsIterator(_ValueIterator):

    kind = 'operand'

    def _dispose(self):
        self._capi.LLVMPY_DisposeOperandsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_OperandsIterNext(self)


# FFI

ffi.lib.LLVMPY_PrintValueToString.argtypes = [
    ffi.LLVMValueRef,
    POINTER(c_char_p)
]

ffi.lib.LLVMPY_GetGlobalParent.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetGlobalParent.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetValueName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetValueName.restype = c_char_p

ffi.lib.LLVMPY_SetValueName.argtypes = [ffi.LLVMValueRef, c_char_p]

ffi.lib.LLVMPY_TypeOf.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_TypeOf.restype = ffi.LLVMTypeRef


ffi.lib.LLVMPY_PrintType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_PrintType.restype = c_void_p

ffi.lib.LLVMPY_TypeIsPointer.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsPointer.restype = c_bool

ffi.lib.LLVMPY_GetElementType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetElementType.restype = ffi.LLVMTypeRef


ffi.lib.LLVMPY_GetTypeName.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeName.restype = c_void_p

ffi.lib.LLVMPY_GetLinkage.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetLinkage.restype = c_int

ffi.lib.LLVMPY_SetLinkage.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetVisibility.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetVisibility.restype = c_int

ffi.lib.LLVMPY_SetVisibility.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetDLLStorageClass.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDLLStorageClass.restype = c_int

ffi.lib.LLVMPY_SetDLLStorageClass.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetEnumAttributeKindForName.argtypes = [c_char_p, c_size_t]
ffi.lib.LLVMPY_GetEnumAttributeKindForName.restype = c_uint

ffi.lib.LLVMPY_AddFunctionAttr.argtypes = [ffi.LLVMValueRef, c_uint]

ffi.lib.LLVMPY_IsDeclaration.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsDeclaration.restype = c_int

ffi.lib.LLVMPY_FunctionAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_CallInstAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_CallInstAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_InvokeInstAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_InvokeInstAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_GlobalAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GlobalAttributesIter.restype = ffi.LLVMAttributeSetIterator

ffi.lib.LLVMPY_ArgumentAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_ArgumentAttributesIter.restype = ffi.LLVMAttributeSetIterator

ffi.lib.LLVMPY_FunctionBlocksIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionBlocksIter.restype = ffi.LLVMBlocksIterator

ffi.lib.LLVMPY_FunctionArgumentsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionArgumentsIter.restype = ffi.LLVMArgumentsIterator

ffi.lib.LLVMPY_BlockInstructionsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_BlockInstructionsIter.restype = ffi.LLVMInstructionsIterator

ffi.lib.LLVMPY_InstructionOperandsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_InstructionOperandsIter.restype = ffi.LLVMOperandsIterator

ffi.lib.LLVMPY_DisposeAttributeListIter.argtypes = [
    ffi.LLVMAttributeListIterator]

ffi.lib.LLVMPY_DisposeAttributeSetIter.argtypes = [ffi.LLVMAttributeSetIterator]

ffi.lib.LLVMPY_DisposeBlocksIter.argtypes = [ffi.LLVMBlocksIterator]

ffi.lib.LLVMPY_DisposeInstructionsIter.argtypes = [ffi.LLVMInstructionsIterator]

ffi.lib.LLVMPY_DisposeOperandsIter.argtypes = [ffi.LLVMOperandsIterator]

ffi.lib.LLVMPY_AttributeListIterNext.argtypes = [ffi.LLVMAttributeListIterator]
ffi.lib.LLVMPY_AttributeListIterNext.restype = c_void_p

ffi.lib.LLVMPY_AttributeSetIterNext.argtypes = [ffi.LLVMAttributeSetIterator]
ffi.lib.LLVMPY_AttributeSetIterNext.restype = c_void_p

ffi.lib.LLVMPY_BlocksIterNext.argtypes = [ffi.LLVMBlocksIterator]
ffi.lib.LLVMPY_BlocksIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_ArgumentsIterNext.argtypes = [ffi.LLVMArgumentsIterator]
ffi.lib.LLVMPY_ArgumentsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_InstructionsIterNext.argtypes = [ffi.LLVMInstructionsIterator]
ffi.lib.LLVMPY_InstructionsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_OperandsIterNext.argtypes = [ffi.LLVMOperandsIterator]
ffi.lib.LLVMPY_OperandsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetOpcodeName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetOpcodeName.restype = c_void_p
