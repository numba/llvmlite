"""
Classes that are LLVM types
"""

from __future__ import annotations

import struct
from typing import Any, Iterable, Iterator

from llvmlite.binding.targets import TargetData
from llvmlite.binding.value import TypeRef
from llvmlite.ir._utils import _StrCaching
from llvmlite.ir.context import Context
from llvmlite.ir.values import Constant, Value


def _wrapname(x: str) -> str:
    return '"{0}"'.format(x.replace('\\', '\\5c').replace('"', '\\22'))


class Type(_StrCaching):
    """
    The base class for all LLVM types.
    """
    is_pointer = False
    null = 'zeroinitializer'

    def __repr__(self) -> str:
        return "<%s %s>" % (type(self), str(self))

    def _to_string(self) -> str:
        raise NotImplementedError

    def as_pointer(self, addrspace: int = 0) -> PointerType:
        # FIXME: either not all types can be pointers or type
        # needs to implement intrinsic_name
        return PointerType(self, addrspace)  # type: ignore

    def __ne__(self, other: object) -> bool:
        return not (self == other)

    # FIXME: target_data is unused?
    def _get_ll_pointer_type(
        self, target_data: TargetData, context: Context | None = None
    ) -> TypeRef:
        """
        Convert this type object to an LLVM type.
        """
        from llvmlite.ir import Module, GlobalVariable
        from llvmlite.binding import parse_assembly

        if context is None:
            m = Module()
        else:
            m = Module(context=context)
        foo = GlobalVariable(m, self, name="foo")
        with parse_assembly(str(m)) as llmod:
            return llmod.get_global_variable(foo.name).type  # type: ignore

    def get_abi_size(
        self, target_data: TargetData, context: Context | None = None
    ) -> int:
        """
        Get the ABI size of this type according to data layout *target_data*.
        """
        llty = self._get_ll_pointer_type(target_data, context)
        return target_data.get_pointee_abi_size(llty)

    def get_abi_alignment(
        self, target_data: TargetData, context: Context | None = None
    ) -> Any:
        """
        Get the minimum ABI alignment of this type according to data layout
        *target_data*.
        """
        llty = self._get_ll_pointer_type(target_data, context)
        return target_data.get_pointee_abi_alignment(llty)

    def format_constant(self, value: float) -> str:
        """
        Format constant *value* of this type.  This method may be overriden
        by subclasses.
        """
        return str(value)

    def wrap_constant_value(self, value: Type | str) -> Type | str:
        """
        Wrap constant *value* if necessary.  This method may be overriden
        by subclasses (especially aggregate types).
        """
        return value

    def __call__(self, value: Type | None) -> Constant:
        """
        Create a LLVM constant of this type with the given Python value.
        """
        return Constant(typ=self, constant=value)


class MetaDataType(Type):
    def _to_string(self) -> str:
        return "metadata"

    # FIXME: invalid method override with Type.as_pointer(self, addrspace)
    def as_pointer(self) -> PointerType:  # type: ignore
        raise TypeError

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MetaDataType)

    def __hash__(self) -> int:
        return hash(MetaDataType)


class LabelType(Type):
    """
    The label type is the type of e.g. basic blocks.
    """

    def _to_string(self) -> str:
        return "label"


class PointerType(Type):
    """
    The type of all pointer values.
    """
    is_pointer = True
    null = 'null'

    def __init__(
        self, pointee: IntType | PointerType | FunctionType, addrspace: int = 0
    ) -> None:
        assert not isinstance(pointee, VoidType)
        self.pointee = pointee
        self.addrspace = addrspace

    def _to_string(self) -> str:
        if self.addrspace != 0:
            return "{0} addrspace({1})*".format(self.pointee, self.addrspace)
        else:
            return "{0}*".format(self.pointee)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PointerType):
            return (self.pointee, self.addrspace) == (other.pointee,
                                                      other.addrspace)
        else:
            return False

    def __hash__(self) -> int:
        return hash(PointerType)

    def gep(self, i: Type) -> Type:
        """
        Resolve the type of the i-th element (for getelementptr lookups).
        """
        if not isinstance(i.type, IntType):  # type: ignore
            raise TypeError(i.type)  # type: ignore
        return self.pointee

    @property
    def intrinsic_name(self) -> str:
        return 'p%d%s' % (self.addrspace, self.pointee.intrinsic_name)  # type: ignore


class VoidType(Type):
    """
    The type for empty values (e.g. a function returning no value).
    """

    def _to_string(self) -> str:
        return 'void'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, VoidType)

    def __hash__(self) -> int:
        return hash(VoidType)


class FunctionType(Type):
    """
    The type for functions.
    """

    def __init__(
        self, return_type: Type, args: Iterable[Type], var_arg: bool = False
    ) -> None:
        self.return_type = return_type
        self.args = tuple(args)
        self.var_arg = var_arg

    def _to_string(self) -> str:
        if self.args:
            strargs = ', '.join([str(a) for a in self.args])
            if self.var_arg:
                return '{0} ({1}, ...)'.format(self.return_type, strargs)
            else:
                return '{0} ({1})'.format(self.return_type, strargs)
        elif self.var_arg:
            return '{0} (...)'.format(self.return_type)
        else:
            return '{0} ()'.format(self.return_type)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FunctionType):
            return (self.return_type == other.return_type and
                    self.args == other.args and self.var_arg == other.var_arg)
        else:
            return False

    def __hash__(self) -> int:
        return hash(FunctionType)


class IntType(Type):
    """
    The type for integers.
    """
    null = '0'
    _instance_cache: dict[int, IntType] = {}
    width: int

    def __new__(cls, bits: int) -> IntType:
        # Cache all common integer types
        if 0 <= bits <= 128:
            try:
                return cls._instance_cache[bits]
            except KeyError:
                inst = cls._instance_cache[bits] = cls.__new(bits)
                return inst
        return cls.__new(bits)

    @classmethod
    def __new(cls, bits: int) -> IntType:
        assert isinstance(bits, int) and bits >= 0
        self = super(IntType, cls).__new__(cls)
        self.width = bits
        return self

    def __getnewargs__(self) -> tuple[int]:
        return self.width,

    def __copy__(self) -> IntType:
        return self

    def _to_string(self) -> str:
        return 'i%u' % (self.width,)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IntType):
            return self.width == other.width
        else:
            return False

    def __hash__(self) -> int:
        return hash(IntType)

    # FIXME: IncompatibleMethodOverride
    def format_constant(self, val: int | bool) -> str:  # type: ignore
        if isinstance(val, bool):
            return str(val).lower()
        else:
            return str(val)

    # FIXME: IncompatibleMethodOverride: val instead of value
    def wrap_constant_value(self, val: int | None) -> int:  # type: ignore
        if val is None:
            return 0
        return val

    @property
    def intrinsic_name(self) -> str:
        return str(self)


def _as_float(value: float) -> float:
    """
    Truncate to single-precision float.
    """
    return struct.unpack('f', struct.pack('f', value))[0]  # type: ignore


def _as_half(value: float) -> float:
    """
    Truncate to half-precision float.
    """
    try:
        return struct.unpack('e', struct.pack('e', value))[0]  # type: ignore
    except struct.error:
        # 'e' only added in Python 3.6+
        return _as_float(value)


def _format_float_as_hex(
    value: float, packfmt: str, unpackfmt: str, numdigits: int
) -> str:
    raw = struct.pack(packfmt, float(value))
    intrep = struct.unpack(unpackfmt, raw)[0]
    out = '{{0:#{0}x}}'.format(numdigits).format(intrep)
    return out


def _format_double(value: float) -> str:
    """
    Format *value* as a hexadecimal string of its IEEE double precision
    representation.
    """
    return _format_float_as_hex(value, 'd', 'Q', 16)


class _BaseFloatType(Type):
    # FIXME: _BaseFloatType doesn't have _instance_cache

    def __new__(cls) -> _BaseFloatType:
        return cls._instance_cache  # type: ignore

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        return hash(type(self))

    @classmethod
    def _create_instance(cls) -> None:
        cls._instance_cache = super(_BaseFloatType, cls).__new__(cls)  # type: ignore


class HalfType(_BaseFloatType):
    """
    The type for single-precision floats.
    """
    null = '0.0'
    intrinsic_name = 'f16'

    def __str__(self) -> str:
        return 'half'

    def format_constant(self, value: float) -> str:
        return _format_double(_as_half(value))


class FloatType(_BaseFloatType):
    """
    The type for single-precision floats.
    """
    null = '0.0'
    intrinsic_name = 'f32'

    def __str__(self) -> str:
        return 'float'

    def format_constant(self, value: float) -> str:
        return _format_double(_as_float(value))


class DoubleType(_BaseFloatType):
    """
    The type for double-precision floats.
    """
    null = '0.0'
    intrinsic_name = 'f64'

    def __str__(self) -> str:
        return 'double'

    def format_constant(self, value: float) -> str:
        return _format_double(value)


for _cls in (HalfType, FloatType, DoubleType):
    _cls._create_instance()


class _Repeat:
    def __init__(self, value: Type, size: int) -> None:
        self.value = value
        self.size = size

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, item: int) -> Type:
        if 0 <= item < self.size:
            return self.value
        else:
            raise IndexError(item)


class VectorType(Type):
    """
    The type for vectors of primitive data items (e.g. "<f32 x 4>").
    """

    def __init__(self, element: Type, count: int) -> None:
        self.element = element
        self.count = count

    @property
    def elements(self) -> _Repeat:
        return _Repeat(self.element, self.count)

    def __len__(self) -> int:
        return self.count

    def _to_string(self) -> str:
        return "<%d x %s>" % (self.count, self.element)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VectorType):
            return self.element == other.element and self.count == other.count
        return False

    def __hash__(self) -> int:
        # TODO: why does this not take self.element/self.count into account?
        return hash(VectorType)

    def __copy__(self) -> VectorType:
        return self

    # FIXME: IncompatibleMethodOverride
    def format_constant(self, value: Iterable[Value]) -> str:  # type: ignore
        itemstring = ", ".join(
            ["{0} {1}".format(x.type, x.get_reference()) for x in value]  # type: ignore
        )
        return "<{0}>".format(itemstring)

    # FIXME: IncompatibleMethodOverride
    def wrap_constant_value(self, values: Iterable[Value]) -> Iterable[Value]:  # type: ignore
        if not isinstance(values, (list, tuple)):
            if isinstance(values, Constant):
                if values.type != self.element:
                    raise TypeError("expected {} for {}".format(
                        self.element, values.type))
                return (values, ) * self.count
            return (Constant(self.element, values), ) * self.count  # type: ignore
        if len(values) != len(self):
            raise ValueError("wrong constant size for %s: got %d elements"
                             % (self, len(values)))
        return [Constant(ty, val) if not isinstance(val, Value) else val
                for ty, val in zip(self.elements, values)]  # type: ignore


class Aggregate(Type):
    """
    Base class for aggregate types.
    See http://llvm.org/docs/LangRef.html#t-aggregate
    """

    # FIXME: does not contain .elements
    # FIXME: does not implement __len__

    # FIXME: IncompatibleMethodOverride
    def wrap_constant_value(self, values: Iterable[Value]) -> Iterable[Value]:  # type: ignore
        if not isinstance(values, (list, tuple)):
            return values
        if len(values) != len(self):  # type: ignore
            raise ValueError("wrong constant size for %s: got %d elements"
                             % (self, len(values)))
        return [Constant(ty, val) if not isinstance(val, Value) else val
                for ty, val in zip(self.elements, values)]  # type: ignore



class ArrayType(Aggregate):
    """
    The type for fixed-size homogenous arrays (e.g. "[f32 x 3]").
    """

    def __init__(self, element: Type, count: int):
        self.element = element
        self.count = count

    @property
    def elements(self) -> _Repeat:
        return _Repeat(self.element, self.count)

    def __len__(self) -> int:
        return self.count

    def _to_string(self) -> str:
        return "[%d x %s]" % (self.count, self.element)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ArrayType):
            return self.element == other.element and self.count == other.count
        return False

    def __hash__(self) -> int:
        return hash(ArrayType)

    def gep(self, i: IntType) -> Type:
        """
        Resolve the type of the i-th element (for getelementptr lookups).
        """
        if not isinstance(i.type, IntType):  # type: ignore
            raise TypeError(i.type)  # type: ignore
        return self.element

    # FIXME: incompatible method overrride
    def format_constant(self, value: Iterable[Value]) -> str:  # type: ignore
        itemstring = ", " .join(["{0} {1}".format(x.type, x.get_reference())  # type: ignore
                                 for x in value])
        return "[{0}]".format(itemstring)


class BaseStructType(Aggregate):
    """
    The base type for heterogenous struct types.
    """
    _packed = False
    # FIXME: BaseStructType has no self.elements

    @property
    def packed(self) -> bool:
        """
        A boolean attribute that indicates whether the structure uses
        packed layout.
        """
        return self._packed

    @packed.setter
    def packed(self, val: bool) -> None:
        self._packed = bool(val)

    def __len__(self) -> int:
        assert self.elements is not None  # type: ignore
        return len(self.elements)  # type: ignore

    def __iter__(self) -> Iterator[Type]:
        assert self.elements is not None  # type: ignore
        return iter(self.elements)  # type: ignore

    @property
    def is_opaque(self) -> bool:
        return self.elements is None  # type: ignore

    def structure_repr(self) -> str:
        """
        Return the LLVM IR for the structure representation
        """
        # BaseStructType has not "elements"
        ret = '{%s}' % ', '.join([str(x) for x in self.elements])  # type: ignore
        return self._wrap_packed(ret)

    # FIXME: incompatible method override
    def format_constant(self, value: Iterable[Value]) -> str:  # type: ignore
        itemstring = ", " .join(["{0} {1}".format(x.type, x.get_reference())  # type: ignore
                                 for x in value])
        ret = "{{{0}}}".format(itemstring)
        return self._wrap_packed(ret)

    def gep(self, i: IntType) -> Type:
        """
        Resolve the type of the i-th element (for getelementptr lookups).

        *i* needs to be a LLVM constant, so that the type can be determined
        at compile-time.
        """
        if not isinstance(i.type, IntType):  # type: ignore
            raise TypeError(i.type)  # type: ignore
        return self.elements[i.constant]  # type: ignore

    def _wrap_packed(self, textrepr: str) -> str:
        """
        Internal helper to wrap textual repr of struct type into packed struct
        """
        if self.packed:
            return '<{}>'.format(textrepr)
        else:
            return textrepr


class LiteralStructType(BaseStructType):
    """
    The type of "literal" structs, i.e. structs with a literally-defined
    type (by contrast with IdentifiedStructType).
    """

    null = 'zeroinitializer'

    def __init__(self, elems: Iterable[Type], packed: bool = False) -> None:
        """
        *elems* is a sequence of types to be used as members.
        *packed* controls the use of packed layout.
        """
        self.elements = tuple(elems)
        self.packed = packed

    def _to_string(self) -> str:
        return self.structure_repr()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LiteralStructType):
            return self.elements == other.elements
        return False

    def __hash__(self) -> int:
        return hash(LiteralStructType)


class IdentifiedStructType(BaseStructType):
    """
    A type which is a named alias for another struct type, akin to a typedef.
    While literal struct types can be structurally equal (see
    LiteralStructType), identified struct types are compared by name.

    Do not use this directly.
    """
    null = 'zeroinitializer'

    def __init__(self, context: Context, name: str, packed: bool = False) -> None:
        """
        *context* is a llvmlite.ir.Context.
        *name* is the identifier for the new struct type.
        *packed* controls the use of packed layout.
        """
        assert name
        self.context = context
        self.name = name
        self.elements: None | tuple[Type, ...] = None
        self.packed = packed

    def _to_string(self) -> str:
        return "%{name}".format(name=_wrapname(self.name))

    def get_declaration(self) -> str:
        """
        Returns the string for the declaration of the type
        """
        if self.is_opaque:
            out = "{strrep} = type opaque".format(strrep=str(self))
        else:
            out = "{strrep} = type {struct}".format(
                strrep=str(self), struct=self.structure_repr())
        return out

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IdentifiedStructType):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(IdentifiedStructType)

    def set_body(self, *elems: Iterable[Type]) -> None:
        if not self.is_opaque:
            raise RuntimeError("{name} is already defined".format(
                name=self.name))
        self.elements = tuple(elems)  # type: ignore
