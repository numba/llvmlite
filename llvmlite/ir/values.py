"""
Classes that are LLVM values: Value, Constant...
Instructions are in the instructions module.
"""

from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING, Any, Iterable, Iterator
from typing import Type as PyType

from llvmlite.ir import _utils, types, values
from llvmlite.ir._utils import _HasMetadata, _StrCaching, _StringReferenceCaching
from llvmlite.ir.module import Module

if TYPE_CHECKING:
    from llvmlite.ir.instructions import Instruction

_VALID_CHARS = (
    frozenset(map(ord, string.ascii_letters))
    | frozenset(map(ord, string.digits))
    | frozenset(map(ord, " !#$%&'()*+,-./:;<=>?@[]^_`{|}~"))
)

_SIMPLE_IDENTIFIER_RE = re.compile(r"[-a-zA-Z$._][-a-zA-Z$._0-9]*$")

_CMP_MAP = {
    ">": "gt",
    "<": "lt",
    "==": "eq",
    "!=": "ne",
    ">=": "ge",
    "<=": "le",
}


def _escape_string(
    text: str | bytes | bytearray,
    _map: dict[int, str] = {},
) -> str:
    """
    Escape the given bytestring for safe use as a LLVM array constant.
    Any unicode string input is first encoded with utf8 into bytes.
    """
    if isinstance(text, str):
        text = text.encode()
    assert isinstance(text, (bytes, bytearray))

    if not _map:
        for ch in range(256):
            if ch in _VALID_CHARS:
                _map[ch] = chr(ch)
            else:
                _map[ch] = f"\\{ch:02x}"

    buf = [_map[ch] for ch in text]
    return "".join(buf)


class _ConstOpMixin:
    """
    A mixin defining constant operations, for use in constant-like classes.
    """

    # FIXME: self.type missing. How to communicate that Mixedin needs this?

    #
    # Arithmetic APIs
    #

    def _binop(self, opname: str, rhs: Constant) -> FormattedConstant:
        if self.type != rhs.type:  # type: ignore
            raise ValueError(
                "Operands must be the same type, got ({0}, {1})".format(
                    self.type,  # type: ignore
                    rhs.type,
                )
            )
        fmt = "{0} ({1} {2}, {3} {4})".format(
            opname,
            self.type,  # type: ignore
            self.get_reference(),  # type: ignore
            rhs.type,
            rhs.get_reference(),
        )
        return FormattedConstant(
            self.type,  # type: ignore
            fmt,
        )

    def _castop(self, opname: str, typ: types.Type) -> Constant:
        # Returns Constant | FormattedConstant, which is a child of Constant
        if typ == self.type:  # type: ignore
            return self  # type: ignore

        op = "{0} ({1} {2} to {3})".format(
            opname,
            self.type,  # type: ignore
            self.get_reference(),  # type: ignore
            typ,
        )
        return FormattedConstant(typ, op)

    def shl(self, other: Constant) -> FormattedConstant:
        """
        Left integer shift:
            lhs << rhs
        """
        return self._binop("shl", other)

    def lshr(self, other: Constant) -> FormattedConstant:
        """
        Logical (unsigned) right integer shift:
            lhs >> rhs
        """
        return self._binop("lshr", other)

    def ashr(self, other: Constant) -> FormattedConstant:
        """
        Arithmetic (signed) right integer shift:
            lhs >> rhs
        """
        return self._binop("ashr", other)

    def add(self, other: Constant) -> FormattedConstant:
        """
        Integer addition:
            lhs + rhs
        """
        return self._binop("add", other)

    def fadd(self, other: Constant) -> FormattedConstant:
        """
        Floating-point addition:
            lhs + rhs
        """
        return self._binop("fadd", other)

    def sub(self, other: Constant) -> FormattedConstant:
        """
        Integer subtraction:
            lhs - rhs
        """
        return self._binop("sub", other)

    def fsub(self, other: Constant) -> FormattedConstant:
        """
        Floating-point subtraction:
            lhs - rhs
        """
        return self._binop("fsub", other)

    def mul(self, other: Constant) -> FormattedConstant:
        """
        Integer multiplication:
            lhs * rhs
        """
        return self._binop("mul", other)

    def fmul(self, other: Constant) -> FormattedConstant:
        """
        Floating-point multiplication:
            lhs * rhs
        """
        return self._binop("fmul", other)

    def udiv(self, other: Constant) -> FormattedConstant:
        """
        Unsigned integer division:
            lhs / rhs
        """
        return self._binop("udiv", other)

    def sdiv(self, other: Constant) -> FormattedConstant:
        """
        Signed integer division:
            lhs / rhs
        """
        return self._binop("sdiv", other)

    def fdiv(self, other: Constant) -> FormattedConstant:
        """
        Floating-point division:
            lhs / rhs
        """
        return self._binop("fdiv", other)

    def urem(self, other: Constant) -> FormattedConstant:
        """
        Unsigned integer remainder:
            lhs % rhs
        """
        return self._binop("urem", other)

    def srem(self, other: Constant) -> FormattedConstant:
        """
        Signed integer remainder:
            lhs % rhs
        """
        return self._binop("srem", other)

    def frem(self, other: Constant) -> FormattedConstant:
        """
        Floating-point remainder:
            lhs % rhs
        """
        return self._binop("frem", other)

    def or_(self, other: Constant) -> FormattedConstant:
        """
        Bitwise integer OR:
            lhs | rhs
        """
        return self._binop("or", other)

    def and_(self, other: Constant) -> FormattedConstant:
        """
        Bitwise integer AND:
            lhs & rhs
        """
        return self._binop("and", other)

    def xor(self, other: Constant) -> FormattedConstant:
        """
        Bitwise integer XOR:
            lhs ^ rhs
        """
        return self._binop("xor", other)

    def _cmp(
        self, prefix: str, sign: str, cmpop: str, other: Constant
    ) -> FormattedConstant:
        ins = prefix + "cmp"
        try:
            op = _CMP_MAP[cmpop]
        except KeyError:
            raise ValueError(f"invalid comparison {cmpop!r} for {ins}")

        if not (prefix == "i" and cmpop in ("==", "!=")):
            op = sign + op

        if self.type != other.type:  # type: ignore
            raise ValueError(
                "Operands must be the same type, got ({0}, {1})".format(
                    self.type,  # type: ignore
                    other.type,
                )
            )

        fmt = "{0} {1} ({2} {3}, {4} {5})".format(
            ins,
            op,
            self.type,  # type: ignore
            self.get_reference(),  # type: ignore
            other.type,
            other.get_reference(),
        )

        return FormattedConstant(types.IntType(1), fmt)

    def icmp_signed(self, cmpop: str, other: Constant) -> FormattedConstant:
        """
        Signed integer comparison:
            lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._cmp("i", "s", cmpop, other)

    def icmp_unsigned(self, cmpop: str, other: Constant) -> FormattedConstant:
        """
        Unsigned integer (or pointer) comparison:
            lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._cmp("i", "u", cmpop, other)

    def fcmp_ordered(self, cmpop: str, other: Constant) -> FormattedConstant:
        """
        Floating-point ordered comparison:
            lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        return self._cmp("f", "o", cmpop, other)

    def fcmp_unordered(self, cmpop: str, other: Constant) -> FormattedConstant:
        """
        Floating-point unordered comparison:
            lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        return self._cmp("f", "u", cmpop, other)

    #
    # Unary APIs
    #

    def not_(self) -> FormattedConstant:
        """
        Bitwise integer complement:
            ~value
        """
        if isinstance(self.type, types.VectorType):  # type: ignore
            rhs = values.Constant(self.type, (-1,) * self.type.count)  # type: ignore
        else:
            rhs = values.Constant(self.type, -1)  # type: ignore

        return self.xor(rhs)

    def neg(self) -> FormattedConstant:
        """
        Integer negative:
            -value
        """
        zero = values.Constant(self.type, 0)  # type: ignore
        return zero.sub(self)  # type: ignore

    def fneg(self) -> FormattedConstant:
        """
        Floating-point negative:
            -value
        """
        fmt = "fneg ({0} {1})".format(self.type, self.get_reference())  # type: ignore
        return FormattedConstant(self.type, fmt)  # type: ignore

    #
    # Cast APIs
    #

    def trunc(self, typ: types.Type) -> Constant:
        """
        Truncating integer downcast to a smaller type.
        """
        return self._castop("trunc", typ)

    def zext(self, typ: types.Type) -> Constant:
        """
        Zero-extending integer upcast to a larger type
        """
        return self._castop("zext", typ)

    def sext(self, typ: types.Type) -> Constant:
        """
        Sign-extending integer upcast to a larger type.
        """
        return self._castop("sext", typ)

    def fptrunc(self, typ: types.Type) -> Constant:
        """
        Floating-point downcast to a less precise type.
        """
        return self._castop("fptrunc", typ)

    def fpext(self, typ: types.Type) -> Constant:
        """
        Floating-point upcast to a more precise type.
        """
        return self._castop("fpext", typ)

    def bitcast(self, typ: types.Type) -> Constant:
        """
        Pointer cast to a different pointer type.
        """
        return self._castop("bitcast", typ)

    def fptoui(self, typ: types.Type) -> Constant:
        """
        Convert floating-point to unsigned integer.
        """
        return self._castop("fptoui", typ)

    def uitofp(self, typ: types.Type) -> Constant:
        """
        Convert unsigned integer to floating-point.
        """
        return self._castop("uitofp", typ)

    def fptosi(self, typ: types.Type) -> Constant:
        """
        Convert floating-point to signed integer.
        """
        return self._castop("fptosi", typ)

    def sitofp(self, typ: types.Type) -> Constant:
        """
        Convert signed integer to floating-point.
        """
        return self._castop("sitofp", typ)

    def ptrtoint(self, typ: types.Type) -> Constant:
        """
        Cast pointer to integer.
        """
        if not isinstance(self.type, types.PointerType):  # type: ignore
            msg = "can only call ptrtoint() on pointer type, not '{}'"
            raise TypeError(msg.format(self.type))  # type: ignore
        if not isinstance(typ, types.IntType):
            raise TypeError(f"can only ptrtoint() to integer type, not '{typ}'")
        return self._castop("ptrtoint", typ)

    def inttoptr(self, typ: types.Type) -> Constant:
        """
        Cast integer to pointer.
        """
        if not isinstance(self.type, types.IntType):  # type: ignore
            raise TypeError(f"can only call inttoptr() on integer constants, not '{self.type}'")  # type: ignore
        if not isinstance(typ, types.PointerType):
            raise TypeError(f"can only inttoptr() to pointer type, not '{typ}'")
        return self._castop("inttoptr", typ)

    def gep(self, indices: list[Constant]) -> FormattedConstant:
        """
        Call getelementptr on this pointer constant.
        """
        if not isinstance(self.type, types.PointerType):  # type: ignore
            raise TypeError(
                f"can only call gep() on pointer constants, not '{self.type}'"  # type: ignore
            )

        outtype = self.type  # type: ignore
        for i in indices:
            outtype = outtype.gep(i)  # type: ignore

        strindices = [f"{idx.type} {idx.get_reference()}" for idx in indices]

        op = "getelementptr ({0}, {1} {2}, {3})".format(
            self.type.pointee,  # type: ignore
            self.type,  # type: ignore
            self.get_reference(),  # type: ignore
            ", ".join(strindices),
        )
        return FormattedConstant(outtype.as_pointer(self.addrspace), op)  # type: ignore


class Value:
    """
    The base class for all values.
    """

    # FIXME: neither .type nor .get_reference() are defined here

    def __repr__(self) -> str:
        return "<ir.{0} type='{1}' ...>".format(
            self.__class__.__name__,
            self.type,  # type: ignore
        )


class _Undefined:
    """
    'undef': a value for undefined values.
    """

    def __new__(cls) -> _Undefined:
        try:
            return Undefined
        except NameError:
            return object.__new__(_Undefined)


Undefined = _Undefined()


class Constant(_StrCaching, _StringReferenceCaching, _ConstOpMixin, Value):
    """
    A constant LLVM value.
    """

    def __init__(
        self,
        typ: types.Type,
        constant: types.Type
        | int
        | str
        | tuple[int, ...]
        | list[Constant]
        | _Undefined
        | bytearray
        | None,
    ) -> None:
        assert isinstance(typ, types.Type)
        assert not isinstance(typ, types.VoidType)
        self.type = typ
        constant = typ.wrap_constant_value(constant)  # type: ignore
        self.constant = constant

    def _to_string(self) -> str:
        return f"{self.type} {self.get_reference()}"

    def _get_reference(self) -> str:
        if self.constant is None:
            val = self.type.null

        elif self.constant is Undefined:
            val = "undef"

        elif isinstance(self.constant, bytearray):
            val = f'c"{_escape_string(self.constant)}"'

        else:
            val = self.type.format_constant(self.constant)  # type: ignore

        return val

    @classmethod
    def literal_array(cls: PyType[Constant], elems: list[Constant]) -> Constant:
        """
        Construct a literal array constant made of the given members.
        """
        tys = [el.type for el in elems]
        if len(tys) == 0:
            raise ValueError("need at least one element")
        ty = tys[0]
        for other in tys:
            if ty != other:
                raise TypeError("all elements must have the same type")
        return cls(types.ArrayType(ty, len(elems)), elems)

    @classmethod
    def literal_struct(cls, elems: list[Constant]) -> Constant:
        """
        Construct a literal structure constant made of the given members.
        """
        tys = [el.type for el in elems]
        return cls(types.LiteralStructType(tys), elems)

    @property
    def addrspace(self) -> int:
        if not isinstance(self.type, types.PointerType):
            raise TypeError("Only pointer constant have address spaces")
        return self.type.addrspace

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Constant):
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        return f"<ir.Constant type='{self.type}' value={self.constant!r}>"


class FormattedConstant(Constant):
    """
    A constant with an already formatted IR representation.
    """

    def __init__(self, typ: types.Type, constant: str) -> None:
        assert isinstance(constant, str)
        Constant.__init__(self, typ, constant)

    def _to_string(self) -> str:
        # FIXME: self.constant can be types.Type!
        return self.constant  # type: ignore

    def _get_reference(self) -> str:
        # FIXME: self.constant can be types.Type!
        return self.constant  # type: ignore


class NamedValue(_StrCaching, _StringReferenceCaching, Value):
    """
    The base class for named values.
    """

    _name: str
    name_prefix = "%"
    deduplicate_name = True

    def __init__(
        self, parent: Module | Function | Block, type: types.Type, name: str
    ) -> None:
        assert parent is not None
        assert isinstance(type, types.Type)
        self.parent = parent
        self.type = type
        self.name = name

    def _to_string(self) -> str:
        buf: list[str] = []
        if not isinstance(self.type, types.VoidType):
            buf.append(f"{self.get_reference()} = ")
        self.descr(buf)
        return "".join(buf).rstrip()

    def descr(self, buf: list[str]) -> None:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        name = self.parent.scope.register(name, deduplicate=self.deduplicate_name)
        self._name = name

    def _get_reference(self) -> str:
        name = self.name
        # Quote and escape value name
        if "\\" in name or '"' in name:
            name = name.replace("\\", "\\5c").replace('"', "\\22")
        return f'{self.name_prefix}"{name}"'

    def __repr__(self) -> str:
        return "<ir.{} {!r} of type '{}'>".format(
            self.__class__.__name__,
            self.name,
            self.type,
        )

    @property
    def function_type(self) -> types.FunctionType:
        ty = self.type
        if isinstance(ty, types.PointerType):
            ty = self.type.pointee  # type: ignore
        if isinstance(ty, types.FunctionType):
            return ty  # type: ignore
        else:
            raise TypeError(f"Not a function: {self.type}")


class MetaDataString(NamedValue):
    """
    A metadata string, i.e. a constant string used as a value in a metadata
    node.
    """

    def __init__(self, parent: Module | Block, string: str) -> None:
        super().__init__(parent, types.MetaDataType(), name="")
        self.string = string

    def descr(self, buf: list[str]) -> None:
        buf += (self.get_reference(), "\n")

    def _get_reference(self) -> str:
        return f'!"{_escape_string(self.string)}"'

    _to_string = _get_reference

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MetaDataString):
            return self.string == other.string
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.string)


class MetaDataArgument(_StrCaching, _StringReferenceCaching, Value):
    """
    An argument value to a function taking metadata arguments.
    This can wrap any other kind of LLVM value.

    Do not instantiate directly, Builder.call() will create these
    automatically.
    """

    def __init__(self, value: Value) -> None:
        assert isinstance(value, Value)
        assert not isinstance(value.type, types.MetaDataType)  # type: ignore
        self.type = types.MetaDataType()
        self.wrapped_value = value

    def _get_reference(self) -> str:
        # e.g. "i32* %2"
        return "{0} {1}".format(
            self.wrapped_value.type,  # type: ignore
            self.wrapped_value.get_reference(),  # type: ignore
        )

    _to_string = _get_reference


class NamedMetaData:
    """
    A named metadata node.

    Do not instantiate directly, use Module.add_named_metadata() instead.
    """

    def __init__(self, parent: Block) -> None:
        self.parent = parent
        self.operands: list[MDValue] = []

    def add(self, md: MDValue) -> None:
        self.operands.append(md)


class MDValue(NamedValue):
    """
    A metadata node's value, consisting of a sequence of elements ("operands").

    Do not instantiate directly, use Module.add_metadata() instead.
    """

    name_prefix = "!"

    def __init__(self, parent: Module, values: list[Constant], name: str) -> None:
        super().__init__(parent, types.MetaDataType(), name=name)
        self.operands = tuple(values)
        parent.metadata.append(self)

    def descr(self, buf: list[str]) -> None:
        operands: list[str] = []
        for op in self.operands:
            if isinstance(op.type, types.MetaDataType):
                if isinstance(op, Constant) and op.constant is None:
                    operands.append("null")
                else:
                    operands.append(op.get_reference())
            else:
                operands.append(f"{op.type} {op.get_reference()}")
        ops = ", ".join(operands)
        buf += (f"!{{ {ops} }}", "\n")

    def _get_reference(self) -> str:
        return self.name_prefix + str(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MDValue):
            return self.operands == other.operands
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.operands)


class DIToken:
    """
    A debug information enumeration value that should appear bare in
    the emitted metadata.

    Use this to wrap known constants, e.g. the DW_* enumerations.
    """

    def __init__(self, value: Constant) -> None:
        self.value = value


class DIValue(NamedValue):
    """
    A debug information descriptor, containing key-value pairs.

    Do not instantiate directly, use Module.add_debug_info() instead.
    """

    name_prefix = "!"

    def __init__(
        self,
        parent: Module,
        is_distinct: bool,
        kind: str,
        operands: Iterable[tuple[str, Value]],
        name: str,
    ) -> None:
        super().__init__(parent, types.MetaDataType(), name=name)
        self.is_distinct = is_distinct
        self.kind = kind
        self.operands: tuple[tuple[str, Value], ...] = tuple(operands)
        parent.metadata.append(self)

    def descr(self, buf: list[str]) -> None:
        if self.is_distinct:
            buf += ("distinct ",)
        operands = []
        for key, value in self.operands:
            if value is None:
                strvalue = "null"
            elif value is True:
                strvalue = "true"
            elif value is False:
                strvalue = "false"
            elif isinstance(value, DIToken):
                strvalue = value.value
            elif isinstance(value, str):
                strvalue = f'"{_escape_string(value)}"'  # type: ignore
            elif isinstance(value, int):
                strvalue = str(value)  # type: ignore
            elif isinstance(value, NamedValue):
                strvalue = value.get_reference()  # type: ignore
            else:
                raise TypeError(f"invalid operand type for debug info: {value!r}")
            operands.append(f"{key}: {strvalue}")  # type: ignore
        ops = ", ".join(operands)
        buf += ("!", self.kind, "(", ops, ")\n")

    def _get_reference(self) -> str:
        return self.name_prefix + str(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DIValue):
            return (
                self.is_distinct == other.is_distinct
                and self.kind == other.kind
                and self.operands == other.operands
            )
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.is_distinct, self.kind, self.operands))


class GlobalValue(NamedValue, _ConstOpMixin, _HasMetadata):
    """
    A global value.
    """

    name_prefix = "@"
    deduplicate_name = False

    def __init__(
        self,
        parent: Module | Block | Function,
        type: types.Type,
        name: str,
    ) -> None:
        super().__init__(parent=parent, type=type, name=name)
        self.linkage = ""
        self.storage_class = ""
        self.section = ""
        self.metadata = {}  # type: ignore


class GlobalVariable(GlobalValue):
    """
    A global variable.
    """

    def __init__(
        self, module: Module, typ: types.Type, name: str, addrspace: int = 0
    ) -> None:
        assert isinstance(typ, types.Type)
        super().__init__(module, typ.as_pointer(addrspace), name=name)  # type: ignore
        self.value_type = typ
        self.initializer = None
        self.unnamed_addr = False
        self.global_constant = False
        self.addrspace = addrspace
        self.align = None
        self.parent.add_global(self)  # type: ignore

    def descr(self, buf: list[str]) -> None:
        if self.global_constant:
            kind = "constant"
        else:
            kind = "global"

        if not self.linkage:
            # Default to external linkage
            linkage = "external" if self.initializer is None else ""
        else:
            linkage = self.linkage

        if linkage:
            buf.append(linkage + " ")
        if self.storage_class:
            buf.append(self.storage_class + " ")
        if self.unnamed_addr:
            buf.append("unnamed_addr ")
        if self.addrspace != 0:
            buf.append(f"addrspace({self.addrspace:d}) ")

        buf.append(f"{kind} {self.value_type}")

        if self.initializer is not None:
            if self.initializer.type != self.value_type:  # type: ignore
                raise TypeError(
                    f"got initializer of type {self.initializer.type} "  # type: ignore
                    f"for global value type {self.value_type}"
                )
            buf.append(" " + self.initializer.get_reference())  # type: ignore
        elif linkage not in ("external", "extern_weak"):
            # emit 'undef' for non-external linkage GV
            buf.append(" " + self.value_type(Undefined).get_reference())  # type: ignore

        if self.section:
            buf.append(f", section {self.section!r}")

        if self.align is not None:
            buf.append(f", align {self.align}")

        if self.metadata:  # type: ignore
            buf.append(self._stringify_metadata(leading_comma=True))

        buf.append("\n")


class AttributeSet(set):  # type: ignore
    """A set of string attribute.
    Only accept items listed in *_known*.

    Properties:
    * Iterate in sorted order
    """

    _known = ()

    def __init__(self, args: tuple[str, ...] | str = ()) -> None:
        if isinstance(args, str):
            args = [args]  # type: ignore
        for name in args:
            self.add(name)

    def add(self, name: str) -> None:
        if name not in self._known:
            raise ValueError(f"unknown attr {name!r} for {self}")
        return super().add(name)  # type: ignore

    def __iter__(self) -> Iterator[str]:
        # In sorted order
        return iter(sorted(super().__iter__()))  # type: ignore


class FunctionAttributes(AttributeSet):
    _known = frozenset(  # type: ignore
        [
            "argmemonly",
            "alwaysinline",
            "builtin",
            "cold",
            "inaccessiblememonly",
            "inaccessiblemem_or_argmemonly",
            "inlinehint",
            "jumptable",
            "minsize",
            "naked",
            "nobuiltin",
            "noduplicate",
            "noimplicitfloat",
            "noinline",
            "nonlazybind",
            "norecurse",
            "noredzone",
            "noreturn",
            "nounwind",
            "optnone",
            "optsize",
            "readnone",
            "readonly",
            "returns_twice",
            "sanitize_address",
            "sanitize_memory",
            "sanitize_thread",
            "ssp",
            "sspreg",
            "sspstrong",
            "uwtable",
        ]
    )

    def __init__(self, args: tuple[str, ...] = ()) -> None:
        self._alignstack: int = 0
        self._personality: GlobalValue | None = None
        super().__init__(args)

    def add(self, name: str) -> None:
        if (name == "alwaysinline" and "noinline" in self) or (
            name == "noinline" and "alwaysinline" in self
        ):
            raise ValueError("Can't have alwaysinline and noinline")

        super().add(name)

    @property
    def alignstack(self) -> int:
        return self._alignstack  # type: ignore

    @alignstack.setter
    def alignstack(self, val: int) -> None:
        assert val >= 0
        self._alignstack = val

    @property
    def personality(self) -> GlobalValue | None:
        return self._personality

    @personality.setter
    def personality(self, val: GlobalValue | None) -> None:
        assert val is None or isinstance(val, GlobalValue)
        self._personality = val

    def __repr__(self) -> str:
        attrs: list[str] = list(self)
        if self.alignstack:
            attrs.append(f"alignstack({self.alignstack:d})")
        if self.personality:
            attrs.append(
                f"personality {self.personality.type} {self.personality.get_reference()}"
            )
        return " ".join(attrs)


class Function(GlobalValue):
    """Represent a LLVM Function but does uses a Module as parent.
    Global Values are stored as a set of dependencies (attribute `depends`).
    """

    parent: Module

    def __init__(self, module: Module, ftype: types.FunctionType, name: str) -> None:
        assert isinstance(ftype, types.Type)
        super().__init__(module, ftype.as_pointer(), name=name)
        self.ftype = ftype
        self.scope = _utils.NameScope()
        self.blocks: list[Block] = []
        self.attributes = FunctionAttributes()
        self.args = tuple([Argument(self, t) for t in ftype.args])  # type: ignore
        self.return_value = ReturnValue(self, ftype.return_type)  # type: ignore
        self.parent.add_global(self)  # type: ignore
        self.calling_convention = ""

    @property
    def module(self) -> Module:
        return self.parent

    @property
    def entry_basic_block(self) -> Block:
        return self.blocks[0]

    @property
    def basic_blocks(self) -> list[Block]:
        return self.blocks

    def append_basic_block(self, name: str = "") -> Block:
        blk = Block(parent=self, name=name)
        self.blocks.append(blk)
        return blk

    def insert_basic_block(self, before: int, name: str = "") -> Block:
        """Insert block before"""
        blk = Block(parent=self, name=name)
        self.blocks.insert(before, blk)
        return blk

    def descr_prototype(self, buf: list[str]) -> None:
        """
        Describe the prototype ("head") of the function.
        """
        state = "define" if self.blocks else "declare"
        ret = self.return_value
        args = ", ".join(str(a) for a in self.args)
        name = self.get_reference()
        self_attrs = self.attributes
        attrs = " {}".format(self_attrs) if self_attrs else ""
        if any(self.args):
            vararg = ", ..." if self.ftype.var_arg else ""
        else:
            vararg = "..." if self.ftype.var_arg else ""
        linkage = self.linkage
        cconv = self.calling_convention
        prefix = " ".join(str(x) for x in [state, linkage, cconv, ret] if x)
        metadata = self._stringify_metadata()
        metadata = " {}".format(metadata) if metadata else ""
        section = ' section "{}"'.format(self.section) if self.section else ""
        pt_str = "{prefix} {name}({args}{vararg}){attrs}{section}{metadata}\n"
        prototype = pt_str.format(
            prefix=prefix,
            name=name,
            args=args,
            vararg=vararg,
            attrs=attrs,
            section=section,
            metadata=metadata,
        )
        buf.append(prototype)

    def descr_body(self, buf: list[str]) -> None:
        """
        Describe of the body of the function.
        """
        for blk in self.blocks:
            blk.descr(buf)

    def descr(self, buf: list[str]) -> None:
        self.descr_prototype(buf)
        if self.blocks:
            buf.append("{\n")
            self.descr_body(buf)
            buf.append("}\n")

    def __str__(self) -> str:
        buf: list[str] = []
        self.descr(buf)
        return "".join(buf)

    @property
    def is_declaration(self) -> bool:
        return len(self.blocks) == 0


class ArgumentAttributes(AttributeSet):
    _known = frozenset(  # type: ignore
        [
            "byval",
            "inalloca",
            "inreg",
            "nest",
            "noalias",
            "nocapture",
            "nonnull",
            "returned",
            "signext",
            "sret",
            "zeroext",
        ]
    )

    def __init__(self, args: tuple[Any, ...] = ()) -> None:
        self._align = 0
        self._dereferenceable = 0
        self._dereferenceable_or_null = 0
        super().__init__(args)

    @property
    def align(self) -> int:
        return self._align

    @align.setter
    def align(self, val: int) -> None:
        assert isinstance(val, int) and val >= 0
        self._align = val

    @property
    def dereferenceable(self) -> int:
        return self._dereferenceable

    @dereferenceable.setter
    def dereferenceable(self, val: int) -> None:
        assert isinstance(val, int) and val >= 0
        self._dereferenceable = val

    @property
    def dereferenceable_or_null(self) -> int:
        return self._dereferenceable_or_null

    @dereferenceable_or_null.setter
    def dereferenceable_or_null(self, val: int) -> None:
        assert isinstance(val, int) and val >= 0
        self._dereferenceable_or_null = val

    def _to_list(self) -> list[str]:
        attrs: list[str] = sorted(self)
        if self.align:
            attrs.append(f"align {self.align:d}")
        if self.dereferenceable:
            attrs.append(f"dereferenceable({self.dereferenceable:d})")
        if self.dereferenceable_or_null:
            attrs.append(f"dereferenceable_or_null({self.dereferenceable_or_null:d})")
        return attrs


class _BaseArgument(NamedValue):
    def __init__(self, parent: Block, type: types.Type, name: str = "") -> None:
        assert isinstance(type, types.Type)
        super().__init__(parent=parent, type=type, name=name)
        self.attributes = ArgumentAttributes()

    def __repr__(self) -> str:
        return "<ir.{0} {1!r} of type {2}>".format(
            self.__class__.__name__,
            self.name,
            self.type,  # type: ignore
        )

    def add_attribute(self, attr: str) -> None:
        self.attributes.add(attr)


class Argument(_BaseArgument):
    """
    The specification of a function argument.
    """

    def __str__(self) -> str:
        attrs = self.attributes._to_list()
        if attrs:
            return "{0} {1} {2}".format(
                self.type, " ".join(attrs), self.get_reference()
            )
        else:
            return f"{self.type} {self.get_reference()}"


class ReturnValue(_BaseArgument):
    """
    The specification of a function's return value.
    """

    def __str__(self) -> str:
        attrs = self.attributes._to_list()
        if attrs:
            return "{0} {1}".format(" ".join(attrs), self.type)
        else:
            return str(self.type)


class Block(NamedValue):
    """
    A LLVM IR basic block. A basic block is a sequence of
    instructions whose execution always goes from start to end.  That
    is, a control flow instruction (branch) can only appear as the
    last instruction, and incoming branches can only jump to the first
    instruction.
    """

    def __init__(self, parent: Function, name: str = "") -> None:
        super().__init__(parent=parent, type=types.LabelType(), name=name)
        self.scope = parent.scope
        self.instructions: list[Instruction] = []
        self.terminator: Instruction | None = None

    @property
    def is_terminated(self) -> bool:
        return self.terminator is not None

    @property
    def function(self) -> Function:
        parent = self.parent
        # FIXME: sure about this?
        if not isinstance(parent, Function):
            raise AttributeError("Parent must be function")
        return parent

    @property
    def module(self) -> Module:
        return self.parent.module  # type: ignore

    def descr(self, buf: list[str]) -> None:
        buf.append(f"{self._format_name()}:\n")
        buf += [f"  {instr}\n" for instr in self.instructions]

    def replace(self, old: Constant, new: Constant) -> None:
        """Replace an instruction"""
        if old.type != new.type:
            raise TypeError("new instruction has a different type")
        pos = self.instructions.index(old)  # type: ignore
        self.instructions.remove(old)  # type: ignore
        self.instructions.insert(pos, new)  # type: ignore

        for bb in self.parent.basic_blocks:  # type: ignore
            for instr in bb.instructions:  # type: ignore
                instr.replace_usage(old, new)  # type: ignore

    def _format_name(self) -> str:
        # Per the LLVM Language Ref on identifiers, names matching the following
        # regex do not need to be quoted: [%@][-a-zA-Z$._][-a-zA-Z$._0-9]*
        # Otherwise, the identifier must be quoted and escaped.
        name = self.name
        if not _SIMPLE_IDENTIFIER_RE.match(name):
            name = name.replace("\\", "\\5c").replace('"', "\\22")
            name = f'"{name}"'
        return name


class BlockAddress(Value):
    """
    The address of a basic block.
    """

    def __init__(self, function: Function, basic_block: Block) -> None:
        assert isinstance(function, Function)
        assert isinstance(basic_block, Block)
        self.type = types.IntType(8).as_pointer()
        self.function = function
        self.basic_block = basic_block

    def __str__(self) -> str:
        return f"{self.type} {self.get_reference()}"

    def get_reference(self) -> str:
        return "blockaddress({0}, {1})".format(
            self.function.get_reference(),
            self.basic_block.get_reference(),
        )
