from ctypes import POINTER, c_char_p, c_int, cast, c_void_p, c_uint
import enum

from . import ffi
from .common import _decode_string, _encode_string


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


class Attribute(enum.Enum):
    # The LLVMAttribute enum from llvm-c/Core.h

    zext = 1 << 0
    sext = 1 << 1
    noreturn = 1 << 2
    inreg = 1 << 3
    structret = 1 << 4
    nounwind = 1 << 5
    noalias = 1 << 6
    byval = 1 << 7
    nest = 1 << 8
    readnone = 1 << 9
    readonly = 1 << 10
    noinline = 1 << 11
    alwaysinline = 1 << 12
    optimizeforsize = 1 << 13
    stackprotect = 1 << 14
    stackprotectreq = 1 << 15

    nocapture = 1 << 21
    noredzone = 1 << 22
    noimplicitfloat = 1 << 23
    naked = 1 << 24
    inlinehint = 1 << 25

    returnstwice = 1 << 29
    uwtable = 1 << 30
    nonlazybind = 1 << 31


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


class _WeakValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value or type.

    Comparable and hashable using the C-pointer value.
    """

    @property
    def _intptr(self):
        """
        Returns C-Pointer as int
        """
        return cast(self._ptr, c_void_p).value

    def __hash__(self):
        return hash(self._intptr)

    def __eq__(self, other):
        # Comparision requires the type equivalence
        if type(self) is type(other):
            return self._intptr == other._intptr


class ValueRef(_WeakValueRef):
    """A weak reference to a LLVM value.

    The ``__new__`` method is defined to downcast the class type to a provide
    additional features in a typesafe fashion.
    """

    def __new__(cls, ptr, module):
        cls = ValueRef

        if ffi.lib.LLVMPY_IsBasicBlock(ptr):
            cls = BasicBlockRef
        elif ffi.lib.LLVMPY_IsUser(ptr):
            cls = UserRef
            if ffi.lib.LLVMPY_IsGlobalValue(ptr):
                cls = GlobalValueRef
                if ffi.lib.LLVMPY_IsFunction(ptr):
                    cls = FunctionRef
            elif ffi.lib.LLVMPY_IsInstruction(ptr):
                cls = InstructionRef

        return object.__new__(cls)

    def __init__(self, ptr, module):
        # Owns the module to prevent it from being released prematurely.
        self._module = module
        super(ValueRef, self).__init__(ptr)

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)

    def __repr__(self):
        return "<{0} {1!r}>".format(type(self).__name__, self.name)

    @property
    def _valueref(self):
        """Override this method to return the pointer as a LLVMValueRef object.
        The LLVM C-API uses different opaque types for some llvm::Value
        subclass.
        """
        return self

    @property
    def type(self):
        """
        Returns the value type of the value
        """
        return TypeRef(ffi.lib.LLVMPY_TypeOf(self._valueref))

    @property
    def module(self):
        """The module this value is defined in.
        """
        return self._module

    @property
    def name(self):
        """
        Returns the name of the value as a string
        """
        return _decode_string(ffi.lib.LLVMPY_GetValueName(self._valueref))

    @name.setter
    def name(self, val):
        """
        Set the name of value
        """
        ffi.lib.LLVMPY_SetValueName(self._valueref, _encode_string(val))


class UserRef(ValueRef):
    """
    A User is a value that depends on other values, which are operands of
    this the user.
    """

    def __init__(self, ptr, module):
        super(UserRef, self).__init__(ptr, module)
        self._count = ffi.lib.LLVMPY_GetNumOperands(self)

    @property
    def operand_count(self):
        """Returns the number of operands"""
        return self._count

    def _normalize_idx(self, idx):
        """Fix negative values and check for bound."""
        if idx < 0:
            idx += self._count
        if 0 > idx >= self._count:
            raise IndexError("index out-of-bound")
        return idx

    def operand(self, idx):
        """Returns the operand value at the given index"""
        idx = self._normalize_idx(idx)
        return ValueRef(ffi.lib.LLVMPY_GetOperand(self, idx), self._module)

    def operand_use(self, idx):
        """Returns the operand use at the given index"""
        idx = self._normalize_idx(idx)
        return UseRef(ffi.lib.LLVMPY_GetOperandUse(self, idx), self._module)


class GlobalValueRef(UserRef):
    @property
    def linkage(self):
        """
        Get the linkage of the global value
        """
        return Linkage(ffi.lib.LLVMPY_GetLinkage(self))

    @linkage.setter
    def linkage(self, value):
        """
        Set the linkage of the global value
        """
        if not isinstance(value, Linkage):
            value = Linkage[value]
        ffi.lib.LLVMPY_SetLinkage(self, value)

    @property
    def visibility(self):
        """
        Get the visibility of the global value
        """
        return Visibility(ffi.lib.LLVMPY_GetVisibility(self))

    @visibility.setter
    def visibility(self, value):
        """
        Set the visibility of the global value
        """
        if not isinstance(value, Visibility):
            value = Visibility[value]
        ffi.lib.LLVMPY_SetVisibility(self, value)

    @property
    def storage_class(self):
        """
        Get the storage class of the global value
        """
        return StorageClass(ffi.lib.LLVMPY_GetDLLStorageClass(self))

    @storage_class.setter
    def storage_class(self, value):
        """
        Set the visibility of the global value
        """
        if not isinstance(value, StorageClass):
            value = StorageClass[value]
        ffi.lib.LLVMPY_SetDLLStorageClass(self, value)


class FunctionRef(GlobalValueRef):
    def add_function_attribute(self, attr):
        """Only works on function value"""
        # XXX unused?
        if not isinstance(attr, Attribute):
            attr = Attribute[attr]
        ffi.lib.LLVMPY_AddFunctionAttr(self, attr.value)

    @property
    def is_declaration(self):
        """Is this global defined in the current module?
        """
        return ffi.lib.LLVMPY_IsDeclaration(self)

    @property
    def entry_basic_block(self):
        """
        Get the entry basic block of a function GlobalValue
        """
        return ValueRef(ffi.lib.LLVMPY_GetEntryBasicBlock(self), self)

    def iter_basic_blocks(self):
        """
        Returns an iterable for each basic block of the function in order
        """
        cur = self.entry_basic_block
        while True:
            yield cur
            try:
                cur = cur.next
            except ValueError:
                break

    @property
    def basic_blocks(self):
        """
        Returns a list of basic block in order
        """
        return list(self.iter_basic_blocks())

    def __iter__(self):
        return iter(self.iter_basic_blocks())


class BasicBlockRef(ValueRef):
    """
    A weak reference to a LLVM BasicBlock.

    LLVM C-API differentiate between LLVMValueRef and LLVMBasicBlockRef.
    Therefore, this class MUST override `_valueref` property to that will
    convert a LLVMBasicBlockRef to a LLVMValueRef.
    """

    @property
    def function(self):
        return ValueRef(ffi.lib.LLVMGetBasicBlockParent(self._ptr), self.module)

    @property
    def _valueref(self):

        return ffi.lib.LLVMPY_BasicBlockAsValue(self)

    @property
    def next(self):
        """The next basic block of the function"""
        return ValueRef(ffi.lib.LLVMPY_GetNextBasicBlock(self), self.module)

    @property
    def prev(self):
        """The previous basic block of the function"""
        return ValueRef(ffi.lib.LLVMPY_GetPreviousBasicBlock(self),
                        self.module)

    @property
    def first_instruction(self):
        """The first instruction in the basic block"""
        return ValueRef(ffi.lib.LLVMPY_GetFirstInstruction(self), self.module)

    @property
    def last_instruction(self):
        """
        The last instruction (the terminator is a well formed basicblock)
        """
        return ValueRef(ffi.lib.LLVMPY_GetLastInstruction(self), self.module)

    def iter_instructions(self):
        """
        Returns an iterable object that yields each instruction of the basic
        block in sequential order.
        """
        cur = self.first_instruction
        while True:
            yield cur
            try:
                cur = cur.next
            except ValueError:
                break

    def __iter__(self):
        return iter(self.iter_instructions())


class InstructionRef(UserRef):
    """
    A weak reference to a LLVM BasicBlock.
    """

    @property
    def is_call(self):
        """Returns True if this is a call instruction"""
        return ffi.lib.LLVMPY_IsCallInst(self)

    @property
    def callee(self):
        """Get the callee for a call instruction."""
        if not self.is_call:
            raise ValueError("not a call instruction")
        return ValueRef(ffi.lib.LLVMPY_GetCalledValue(self), self._module)

    @property
    def basic_block(self):
        """Get the parent basic block"""
        return ValueRef(ffi.lib.LLVMPY_GetInstructionParent(self), self._module)

    @property
    def function(self):
        """Get the parent function"""
        return self.basic_block.function

    @property
    def next(self):
        """
        Get the next instruction.
        Raise ValueError if this is the last instruction.
        """
        return ValueRef(ffi.lib.LLVMPY_GetNextInstruction(self), self.module)

    @property
    def prev(self):
        """
        Get the previous instruction.
        Raise ValueError if this is the first instruction.
        """
        return ValueRef(ffi.lib.LLVMPY_GetPreviousInstruction(self),
                        self.module)

    @property
    def first_use(self):
        """Returns the first use of this value"""
        try:
            return UseRef(ffi.lib.LLVMPY_GetFirstUse(self), self)
        except ValueError:
            return None


class UseRef(_WeakValueRef):
    """A Use forms a singly-linked-list of usage information.
     Each Use object contains refers to the value being used and the User.
    """

    def __init__(self, ptr, module):
        self._module = module
        super(UseRef, self).__init__(ptr)

    @property
    def value(self):
        """The used value"""
        return ValueRef(ffi.lib.LLVMPY_GetUsedValue(self), self._module)

    @property
    def next(self):
        """The next usage"""
        try:
            return UseRef(ffi.lib.LLVMPY_GetNextUse(self), self.value)
        except ValueError:
            return None

    @property
    def user(self):
        """The user value"""
        return ValueRef(ffi.lib.LLVMPY_GetUser(self), self._module)


class TypeRef(_WeakValueRef):
    """
    A weak reference to a LLVM Type
    """

    def __init__(self, ptr):
        super(TypeRef, self).__init__(ptr)
        self._id = ffi.lib.LLVMPY_TypeID(self)
        with ffi.OutputString() as out:
            ffi.lib.LLVMPY_PrintType(self, out)
            self._str = str(out)

    def __str__(self):
        return self._str

    @property
    def id(self):
        return self._id

    @property
    def pointee(self):
        assert self.is_pointer
        return TypeRef(ffi.lib.LLVMPY_TypePointee(self))

    @property
    def is_pointer(self):
        return bool(ffi.lib.LLVMPY_IsPointerType(self))

    @property
    def is_function(self):
        return bool(ffi.lib.LLVMPY_IsFunctionType(self))

    @property
    def is_function_pointer(self):
        return self.is_pointer and self.pointee.is_function

    @property
    def is_basic_block(self):
        return bool(ffi.lib.LLVMPY_IsLabelType(self))


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

ffi.lib.LLVMPY_GetLinkage.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetLinkage.restype = c_int

ffi.lib.LLVMPY_SetLinkage.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetVisibility.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetVisibility.restype = c_int

ffi.lib.LLVMPY_SetVisibility.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetDLLStorageClass.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDLLStorageClass.restype = c_int

ffi.lib.LLVMPY_SetDLLStorageClass.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_AddFunctionAttr.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_IsDeclaration.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsDeclaration.restype = c_int

ffi.lib.LLVMPY_TypeID.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeID.restype = c_int

ffi.lib.LLVMPY_PrintType.argtypes = [ffi.LLVMTypeRef, POINTER(c_char_p)]

for _is_type_xxx_api in [ffi.lib.LLVMPY_IsFunctionType,
                         ffi.lib.LLVMPY_IsPointerType,
                         ffi.lib.LLVMPY_IsLabelType]:
    _is_type_xxx_api.argtypes = [ffi.LLVMTypeRef]
    _is_type_xxx_api.restype = c_int
del _is_type_xxx_api

ffi.lib.LLVMPY_TypePointee.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypePointee.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetEntryBasicBlock.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetEntryBasicBlock.restype = ffi.LLVMBasicBlockRef

ffi.lib.LLVMPY_GetNextBasicBlock.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_GetNextBasicBlock.restype = ffi.LLVMBasicBlockRef

ffi.lib.LLVMPY_GetPreviousBasicBlock.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_GetPreviousBasicBlock.restype = ffi.LLVMBasicBlockRef

ffi.lib.LLVMPY_ValueAsBasicBlock.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_ValueAsBasicBlock.restype = ffi.LLVMBasicBlockRef

ffi.lib.LLVMPY_BasicBlockAsValue.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_BasicBlockAsValue.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetFirstInstruction.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_GetFirstInstruction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetLastInstruction.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_GetLastInstruction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetNextInstruction.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetNextInstruction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetPreviousInstruction.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetPreviousInstruction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetFirstUse.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetFirstUse.restype = ffi.LLVMUseRef

ffi.lib.LLVMPY_GetNextUse.argtypes = [ffi.LLVMUseRef]
ffi.lib.LLVMPY_GetNextUse.restype = ffi.LLVMUseRef

ffi.lib.LLVMPY_GetUser.argtypes = [ffi.LLVMUseRef]
ffi.lib.LLVMPY_GetUser.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetUsedValue.argtypes = [ffi.LLVMUseRef]
ffi.lib.LLVMPY_GetUsedValue.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetInstructionParent.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetInstructionParent.restype = ffi.LLVMBasicBlockRef

ffi.lib.LLVMPY_GetBasicBlockParent.argtypes = [ffi.LLVMBasicBlockRef]
ffi.lib.LLVMPY_GetBasicBlockParent.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetCalledValue.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetCalledValue.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetOperand.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_GetOperand.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetOperandUse.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_GetOperandUse.restype = ffi.LLVMUseRef

ffi.lib.LLVMPY_GetNumOperands.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetNumOperands.restype = c_int
