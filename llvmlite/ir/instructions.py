"""
Implementation of LLVM IR instructions.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from typing_extensions import Literal

from llvmlite.ir import types
from llvmlite.ir._utils import _HasMetadata
from llvmlite.ir.module import Module
from llvmlite.ir.values import (
    ArgumentAttributes,
    AttributeSet,
    Block,
    Constant,
    Function,
    MetaDataArgument,
    MetaDataString,
    NamedValue,
    Undefined,
    Value,
)


class Instruction(NamedValue, _HasMetadata):
    def __init__(
        self,
        parent: Module | Block,
        typ: types.Type,
        opname: str,
        operands: list[Value],
        name: str = "",
        flags: Iterable[Any] = (),
    ) -> None:
        super().__init__(parent, typ, name=name)
        assert isinstance(parent, Block)
        assert isinstance(flags, (tuple, list))
        self.opname = opname
        self.operands = operands
        self.flags = list(flags)
        self.metadata: dict[str, Any] = {}

    @property
    def function(self) -> Function:
        return self.parent.function  # type: ignore

    @property
    def module(self) -> Module:
        return self.parent.function.module  # type: ignore

    def descr(self, buf: list[str]) -> None:
        opname = self.opname
        if self.flags:
            opname = " ".join([opname] + self.flags)
        operands = ", ".join([op.get_reference() for op in self.operands])  # type: ignore
        typ = self.type
        metadata = self._stringify_metadata(leading_comma=True)
        buf.append("{0} {1} {2}{3}\n".format(opname, typ, operands, metadata))

    def replace_usage(self, old: Constant, new: Constant) -> None:
        if old in self.operands:
            ops: list[Value] = []
            for op in self.operands:
                ops.append(new if op is old else op)
            self.operands = ops
            self._clear_string_cache()

    def __repr__(self) -> str:
        return "<ir.{} {!r} of type '{}', opname {!r}, operands {!r}>".format(
            self.__class__.__name__,
            self.name,
            self.type,
            self.opname,
            self.operands,
        )


class CallInstrAttributes(AttributeSet):
    # FIXME: _known is tuple in AttributeSet
    _known = frozenset(  # type: ignore
        ["noreturn", "nounwind", "readonly", "readnone", "noinline", "alwaysinline"]
    )


class FastMathFlags(AttributeSet):
    # FIXME: _known is tuple in AttributeSet
    _known = frozenset(  # type: ignore
        ["fast", "nnan", "ninf", "nsz", "arcp", "contract", "afn", "reassoc"]
    )


class CallInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        func: Function | InlineAsm,
        args: Sequence[Constant | MetaDataArgument | Function],
        name: str = "",
        cconv: str | None = None,
        tail: bool = False,
        fastmath: tuple[str, ...] = (),
        attrs: tuple[Any, ...] = (),
        arg_attrs: dict[int, tuple[Any, ...]] | None = None,
    ):
        self.cconv = (
            func.calling_convention
            if cconv is None and isinstance(func, Function)
            else cconv
        )
        self.tail = tail
        self.fastmath = FastMathFlags(fastmath)
        self.attributes = CallInstrAttributes(attrs)
        self.arg_attributes: dict[int, ArgumentAttributes] = {}
        if arg_attrs:
            for idx, attrs in arg_attrs.items():
                if not (0 <= idx < len(args)):
                    raise ValueError("Invalid argument index {}".format(idx))
                self.arg_attributes[idx] = ArgumentAttributes(attrs)

        # Fix and validate arguments
        # FIXME: InlineASM has no function_type
        args = list(args)
        for i in range(len(func.function_type.args)):  # type: ignore
            arg = args[i]
            expected_type = func.function_type.args[i]  # type: ignore
            if (
                isinstance(expected_type, types.MetaDataType)
                and arg.type != expected_type
            ):
                arg = MetaDataArgument(arg)
            if arg.type != expected_type:
                msg = "Type of #{0} arg mismatch: {1} != {2}".format(
                    1 + i, expected_type, arg.type
                )
                raise TypeError(msg)
            args[i] = arg

        super().__init__(
            parent=parent,
            typ=func.function_type.return_type,  # type: ignore
            opname="call",
            operands=[func] + list(args),  # type: ignore
            name=name,
        )

    @property
    def callee(self) -> Function:
        # FIXME: this can only ever by Function, not Constant | MetaDataArgument
        return self.operands[0]  # type: ignore

    @callee.setter
    def callee(self, newcallee: Function) -> None:
        self.operands[0] = newcallee

    @property
    def args(self) -> list[Value]:
        return self.operands[1:]

    def replace_callee(self, newfunc: Function) -> None:
        if newfunc.function_type != self.callee.function_type:
            raise TypeError("New function has incompatible type")
        self.callee = newfunc

    @property
    def called_function(self) -> Constant | Function | MetaDataArgument:
        """Alias for llvmpy"""
        return self.callee

    def _descr(self, buf: list[str], add_metadata: bool) -> None:
        def descr_arg(i: int, a: Any) -> str:
            if i in self.arg_attributes:
                attrs = " ".join(self.arg_attributes[i]._to_list()) + " "
            else:
                attrs = ""
            return "{0} {1}{2}".format(a.type, attrs, a.get_reference())

        args = ", ".join([descr_arg(i, a) for i, a in enumerate(self.args)])

        fnty = self.callee.function_type
        # Only print function type if variable-argument
        if fnty.var_arg:
            ty: types.Type = fnty
        # Otherwise, just print the return type.
        else:
            # Fastmath flag work only in this case
            ty = fnty.return_type
        callee_ref = "{0} {1}".format(ty, self.callee.get_reference())
        if self.cconv:
            callee_ref = "{0} {1}".format(self.cconv, callee_ref)
        buf.append(
            "{tail}{op}{fastmath} {callee}({args}){attr}{meta}\n".format(
                tail="tail " if self.tail else "",
                op=self.opname,
                callee=callee_ref,
                fastmath="".join([" " + attr for attr in self.fastmath]),  # type: ignore
                args=args,
                attr="".join([" " + attr for attr in self.attributes]),  # type: ignore
                meta=(
                    self._stringify_metadata(leading_comma=True) if add_metadata else ""
                ),
            )
        )

    def descr(self, buf: list[str]) -> None:
        self._descr(buf, add_metadata=True)


class InvokeInstr(CallInstr):
    def __init__(
        self,
        parent: Block,
        func: Function,
        args: Sequence[Constant | MetaDataArgument | Function],
        normal_to: Block,
        unwind_to: Block,
        name: str = "",
        cconv: str | None = None,
        fastmath: tuple[str, ...] = (),
        attrs: tuple[Any, ...] = (),
        arg_attrs: dict[int, tuple[Any, ...]] | None = None,
    ) -> None:
        assert isinstance(normal_to, Block)
        assert isinstance(unwind_to, Block)
        super().__init__(
            parent,
            func,
            args,
            name,
            cconv,
            tail=False,
            fastmath=fastmath,
            attrs=attrs,
            arg_attrs=arg_attrs,
        )
        self.opname = "invoke"
        self.normal_to = normal_to
        self.unwind_to = unwind_to

    def descr(self, buf: list[str]) -> None:
        super()._descr(buf, add_metadata=False)
        buf.append(
            "      to label {0} unwind label {1}{metadata}\n".format(
                self.normal_to.get_reference(),
                self.unwind_to.get_reference(),
                metadata=self._stringify_metadata(leading_comma=True),
            )
        )


class Terminator(Instruction):
    def __init__(
        self,
        parent: Block,
        opname: str,
        operands: list[Value],
    ) -> None:
        super().__init__(parent, types.VoidType(), opname, operands)

    def descr(self, buf: list[str]) -> None:
        opname = self.opname
        operands = ", ".join(
            ["{0} {1}".format(op.type, op.get_reference()) for op in self.operands]  # type: ignore
        )
        metadata = self._stringify_metadata(leading_comma=True)
        buf.append("{0} {1}{2}".format(opname, operands, metadata))


class PredictableInstr(Instruction):
    def set_weights(self, weights: Iterable[int]) -> None:
        operands: list[Constant] = [MetaDataString(self.module, "branch_weights")]  # type: ignore
        for w in weights:
            if w < 0:
                raise ValueError("branch weight must be a positive integer")
            operands.append(Constant(types.IntType(32), w))
        md = self.module.add_metadata(operands)
        self.set_metadata("prof", md)


class Ret(Terminator):
    def __init__(
        self,
        parent: Block,
        opname: str,
        return_value: Value | None = None,
    ) -> None:
        operands = [return_value] if return_value is not None else []
        super().__init__(parent, opname, operands)

    @property
    def return_value(self) -> Value | None:
        if self.operands:
            return self.operands[0]
        else:
            return None

    def descr(self, buf: list[str]) -> None:
        return_value = self.return_value
        metadata = self._stringify_metadata(leading_comma=True)
        if return_value is not None:
            buf.append(
                "{0} {1} {2}{3}\n".format(
                    self.opname,
                    return_value.type,  # type: ignore
                    return_value.get_reference(),  # type: ignore
                    metadata,
                )
            )
        else:
            buf.append("{0}{1}\n".format(self.opname, metadata))


class Branch(Terminator):
    pass


class ConditionalBranch(PredictableInstr, Terminator):
    pass


class IndirectBranch(PredictableInstr, Terminator):
    def __init__(self, parent: Block, opname: str, addr: Block) -> None:
        super().__init__(parent, opname, [addr])
        self.destinations: list[Block] = []

    @property
    def address(self) -> Value:
        return self.operands[0]

    def add_destination(self, block: Block) -> None:
        assert isinstance(block, Block)
        self.destinations.append(block)

    def descr(self, buf: list[str]) -> None:
        destinations = [
            "label {0}".format(blk.get_reference()) for blk in self.destinations
        ]
        buf.append(
            "indirectbr {0} {1}, [{2}]  {3}\n".format(
                self.address.type,  # type: ignore
                self.address.get_reference(),  # type: ignore
                ", ".join(destinations),
                self._stringify_metadata(leading_comma=True),
            )
        )


class SwitchInstr(PredictableInstr, Terminator):
    def __init__(self, parent: Block, opname: str, val: Value, default: Value) -> None:
        super().__init__(parent, opname, [val])
        self.default = default
        self.cases: list[tuple[Value, Block]] = []

    @property
    def value(self) -> Value:
        return self.operands[0]

    def add_case(self, val: Value, block: Block) -> None:
        assert isinstance(block, Block)
        if not isinstance(val, Value):
            val = Constant(self.value.type, val)  # type: ignore
        self.cases.append((val, block))

    def descr(self, buf: list[str]) -> None:
        cases = [
            "{0} {1}, label {2}".format(
                val.type, val.get_reference(), blk.get_reference()  # type: ignore
            )
            for val, blk in self.cases
        ]
        buf.append(
            "switch {0} {1}, label {2} [{3}]  {4}\n".format(
                self.value.type,  # type: ignore
                self.value.get_reference(),  # type: ignore
                self.default.get_reference(),  # type: ignore
                " ".join(cases),
                self._stringify_metadata(leading_comma=True),
            )
        )


class Resume(Terminator):
    pass


class SelectInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        cond: Constant,
        lhs: Constant,
        rhs: Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> None:
        assert lhs.type == rhs.type
        super().__init__(
            parent, lhs.type, "select", [cond, lhs, rhs], name=name, flags=flags
        )

    @property
    def cond(self) -> Value:
        return self.operands[0]

    @property
    def lhs(self) -> Value:
        return self.operands[1]

    @property
    def rhs(self) -> Value:
        return self.operands[2]

    def descr(self, buf: list[str]) -> None:
        buf.append(
            "select {0} {1} {2}, {3} {4}, {5} {6} {7}\n".format(
                " ".join(self.flags),
                self.cond.type,  # type: ignore
                self.cond.get_reference(),  # type: ignore
                self.lhs.type,  # type: ignore
                self.lhs.get_reference(),  # type: ignore
                self.rhs.type,  # type: ignore
                self.rhs.get_reference(),  # type: ignore
                self._stringify_metadata(leading_comma=True),
            )
        )


class CompareInstr(Instruction):
    # Define the following in subclasses
    OPNAME = "invalid-compare"
    VALID_OP: dict[str, str] = {}
    # FIXME: VALID_FLAG is missing

    def __init__(
        self,
        parent: Block,
        op: str,
        lhs: Constant,
        rhs: Constant,
        name: str = "",
        flags: list[Any] = [],
    ) -> None:
        # FIXME: mutable container as default argument
        # FIXME: why is flags a list here?
        if op not in self.VALID_OP:
            raise ValueError("invalid comparison {!r} for {}".format(op, self.OPNAME))
        for flag in flags:
            if flag not in self.VALID_FLAG:  # type: ignore
                raise ValueError("invalid flag {!r} for {}".format(flag, self.OPNAME))
        opname = self.OPNAME
        if isinstance(lhs.type, types.VectorType):
            typ: types.Type = types.VectorType(types.IntType(1), lhs.type.count)
        else:
            typ = types.IntType(1)
        super().__init__(parent, typ, opname, [lhs, rhs], flags=flags, name=name)
        self.op = op

    def descr(self, buf: list[str]) -> None:
        buf.append(
            "{opname}{flags} {op} {ty} {lhs}, {rhs} {meta}\n".format(
                opname=self.opname,
                flags="".join(" " + it for it in self.flags),
                op=self.op,
                ty=self.operands[0].type,  # type: ignore
                lhs=self.operands[0].get_reference(),  # type: ignore
                rhs=self.operands[1].get_reference(),  # type: ignore
                meta=self._stringify_metadata(leading_comma=True),
            )
        )


class ICMPInstr(CompareInstr):
    OPNAME = "icmp"
    VALID_OP = {
        "eq": "equal",
        "ne": "not equal",
        "ugt": "unsigned greater than",
        "uge": "unsigned greater or equal",
        "ult": "unsigned less than",
        "ule": "unsigned less or equal",
        "sgt": "signed greater than",
        "sge": "signed greater or equal",
        "slt": "signed less than",
        "sle": "signed less or equal",
    }
    VALID_FLAG: set[str] = set()


class FCMPInstr(CompareInstr):
    OPNAME = "fcmp"
    VALID_OP = {
        "false": "no comparison, always returns false",
        "oeq": "ordered and equal",
        "ogt": "ordered and greater than",
        "oge": "ordered and greater than or equal",
        "olt": "ordered and less than",
        "ole": "ordered and less than or equal",
        "one": "ordered and not equal",
        "ord": "ordered (no nans)",
        "ueq": "unordered or equal",
        "ugt": "unordered or greater than",
        "uge": "unordered or greater than or equal",
        "ult": "unordered or less than",
        "ule": "unordered or less than or equal",
        "une": "unordered or not equal",
        "uno": "unordered (either nans)",
        "true": "no comparison, always returns true",
    }
    VALID_FLAG = {"nnan", "ninf", "nsz", "arcp", "contract", "afn", "reassoc", "fast"}


class CastInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        op: str,
        val: Value,
        typ: types.Type,
        name: str = "",
    ) -> None:
        super().__init__(parent, typ, op, [val], name=name)

    def descr(self, buf: list[str]) -> None:
        buf.append(
            "{0} {1} {2} to {3} {4}\n".format(
                self.opname,
                self.operands[0].type,  # type: ignore
                self.operands[0].get_reference(),  # type: ignore
                self.type,
                self._stringify_metadata(leading_comma=True),
            )
        )


class LoadInstr(Instruction):
    def __init__(self, parent: Block, ptr: Value, name: str = "") -> None:
        super().__init__(
            parent,
            ptr.type.pointee,  # type: ignore
            "load",
            [ptr],
            name=name,
        )
        self.align: int | None = None

    def descr(self, buf: list[str]) -> None:
        [val] = self.operands
        if self.align is not None:
            align = f", align {self.align}"
        else:
            align = ""
        buf.append(
            "load {0}, {1} {2}{3}{4}\n".format(
                val.type.pointee,  # type: ignore
                val.type,  # type: ignore
                val.get_reference(),  # type: ignore
                align,
                self._stringify_metadata(leading_comma=True),
            )
        )


class StoreInstr(Instruction):
    def __init__(self, parent: Block, val: Value, ptr: Value) -> None:
        super().__init__(parent, types.VoidType(), "store", [val, ptr])
        self.align: int | None = None

    def descr(self, buf: list[str]) -> None:
        val, ptr = self.operands
        if self.align is not None:
            align = f", align {self.align}"
        else:
            align = ""
        buf.append(
            "store {0} {1}, {2} {3}{4}{5}\n".format(
                val.type,  # type: ignore
                val.get_reference(),  # type: ignore
                ptr.type,  # type: ignore
                ptr.get_reference(),  # type: ignore
                align,
                self._stringify_metadata(leading_comma=True),
            )
        )


class LoadAtomicInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        ptr: Value,
        ordering: str,
        align: int,
        name: str = "",
    ) -> None:
        super().__init__(
            parent,
            ptr.type.pointee,  # type: ignore
            "load atomic",
            [ptr],
            name=name,
        )
        self.ordering = ordering
        self.align = align

    def descr(self, buf: list[str]) -> None:
        [val] = self.operands
        buf.append(
            "load atomic {0}, {1} {2} {3}, align {4}{5}\n".format(
                val.type.pointee,  # type: ignore
                val.type,  # type: ignore
                val.get_reference(),  # type: ignore
                self.ordering,
                self.align,
                self._stringify_metadata(leading_comma=True),
            )
        )


class StoreAtomicInstr(Instruction):
    def __init__(
        self, parent: Block, val: Value, ptr: Value, ordering: str, align: int
    ) -> None:
        super().__init__(parent, types.VoidType(), "store atomic", [val, ptr])
        self.ordering = ordering
        self.align = align

    def descr(self, buf: list[str]) -> None:
        val, ptr = self.operands
        buf.append(
            "store atomic {0} {1}, {2} {3} {4}, align {5}{6}\n".format(
                val.type,  # type: ignore
                val.get_reference(),  # type: ignore
                ptr.type,  # type: ignore
                ptr.get_reference(),  # type: ignore
                self.ordering,
                self.align,
                self._stringify_metadata(leading_comma=True),
            )
        )


class AllocaInstr(Instruction):
    def __init__(
        self, parent: Block, typ: types.Type, count: Value | None, name: str
    ) -> None:
        operands = [count] if count else []
        super().__init__(
            parent,
            typ.as_pointer(),
            "alloca",
            operands,
            name,
        )
        self.align = None

    def descr(self, buf: list[str]) -> None:
        buf.append("{0} {1}".format(self.opname, self.type.pointee))  # type: ignore
        if self.operands:
            (op,) = self.operands
            buf.append(", {0} {1}".format(op.type, op.get_reference()))  # type: ignore
        if self.align is not None:
            buf.append(", align {0}".format(self.align))
        if self.metadata:  # type: ignore
            buf.append(self._stringify_metadata(leading_comma=True))


class GEPInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        ptr: Constant,
        indices: list[Constant],
        inbounds: bool,
        name: str,
    ) -> None:
        typ = ptr.type
        lasttyp = None
        lastaddrspace = 0
        for i in indices:
            lasttyp, typ = typ, typ.gep(i)  # type: ignore
            # inherit the addrspace from the last seen pointer
            if isinstance(lasttyp, types.PointerType):
                lastaddrspace = lasttyp.addrspace  # type: ignore

        if not isinstance(typ, types.PointerType) and isinstance(
            lasttyp, types.PointerType
        ):
            typ = lasttyp  # type: ignore
        else:
            typ = typ.as_pointer(lastaddrspace)  # type: ignore

        super().__init__(
            parent, typ, "getelementptr", [ptr] + list(indices), name=name  # type: ignore
        )
        self.pointer = ptr
        self.indices = indices
        self.inbounds = inbounds

    def descr(self, buf: list[str]) -> None:
        indices = ["{0} {1}".format(i.type, i.get_reference()) for i in self.indices]
        op = "getelementptr inbounds" if self.inbounds else "getelementptr"
        buf.append(
            "{0} {1}, {2} {3}, {4} {5}\n".format(
                op,
                self.pointer.type.pointee,  # type: ignore
                self.pointer.type,
                self.pointer.get_reference(),
                ", ".join(indices),
                self._stringify_metadata(leading_comma=True),
            )
        )


class PhiInstr(Instruction):
    def __init__(
        self,
        parent: Block,
        typ: types.Type,
        name: str,
        flags: tuple[Any, ...] = (),
    ) -> None:
        super().__init__(
            parent=parent,
            typ=typ,
            opname="phi",
            operands=[],
            name=name,
            flags=flags,
        )
        self.incomings: list[tuple[Constant, Block]] = []

    def descr(self, buf: list[str]) -> None:
        incs = ", ".join(
            "[{0}, {1}]".format(v.get_reference(), b.get_reference())
            for v, b in self.incomings
        )
        buf.append(
            "phi {0} {1} {2} {3}\n".format(
                " ".join(self.flags),
                self.type,
                incs,
                self._stringify_metadata(leading_comma=True),
            )
        )

    def add_incoming(self, value: Constant, block: Block) -> None:
        assert isinstance(block, Block)
        self.incomings.append((value, block))

    def replace_usage(self, old: Constant, new: Constant) -> None:
        self.incomings = [
            ((new if val is old else val), blk) for (val, blk) in self.incomings
        ]


class ExtractElement(Instruction):
    def __init__(
        self,
        parent: Block,
        vector: Constant,
        index: Constant,
        name: str = "",
    ) -> None:
        if not isinstance(vector.type, types.VectorType):
            raise TypeError("vector needs to be of VectorType.")
        if not isinstance(index.type, types.IntType):
            raise TypeError("index needs to be of IntType.")
        typ = vector.type.element
        super().__init__(parent, typ, "extractelement", [vector, index], name=name)

    def descr(self, buf: list[str]) -> None:
        operands = ", ".join(
            "{0} {1}".format(op.type, op.get_reference()) for op in self.operands  # type: ignore
        )
        buf.append(
            "{opname} {operands}\n".format(opname=self.opname, operands=operands)
        )


class InsertElement(Instruction):
    def __init__(
        self,
        parent: Block,
        vector: Constant,
        value: Constant,
        index: Constant,
        name: str = "",
    ) -> None:
        if not isinstance(vector.type, types.VectorType):
            raise TypeError("vector needs to be of VectorType.")
        if not value.type == vector.type.element:
            raise TypeError(
                "value needs to be of type {} not {}.".format(
                    vector.type.element, value.type
                )
            )
        if not isinstance(index.type, types.IntType):
            raise TypeError("index needs to be of IntType.")
        typ = vector.type
        super().__init__(
            parent, typ, "insertelement", [vector, value, index], name=name
        )

    def descr(self, buf: list[str]) -> None:
        operands = ", ".join(
            "{0} {1}".format(op.type, op.get_reference()) for op in self.operands  # type: ignore
        )
        buf.append(
            "{opname} {operands}\n".format(opname=self.opname, operands=operands)
        )


class ShuffleVector(Instruction):
    def __init__(
        self,
        parent: Block,
        vector1: Constant,
        vector2: Constant,
        mask: Constant,
        name: str = "",
    ) -> None:
        if not isinstance(vector1.type, types.VectorType):
            raise TypeError("vector1 needs to be of VectorType.")
        if vector2 != Undefined:
            if vector2.type != vector1.type:
                raise TypeError(
                    "vector2 needs to be " + "Undefined or of the same type as vector1."
                )
        if (
            not isinstance(mask, Constant)
            or not isinstance(mask.type, types.VectorType)
            or not (
                isinstance(mask.type.element, types.IntType)
                and mask.type.element.width == 32
            )
        ):
            raise TypeError("mask needs to be a constant i32 vector.")
        typ = types.VectorType(vector1.type.element, mask.type.count)
        index_range = range(
            vector1.type.count if vector2 == Undefined else 2 * vector1.type.count
        )
        if not all(ii.constant in index_range for ii in mask.constant):  # type: ignore
            raise IndexError(
                "mask values need to be in {0}".format(index_range),
            )
        super().__init__(
            parent, typ, "shufflevector", [vector1, vector2, mask], name=name
        )

    def descr(self, buf: list[str]) -> None:
        buf.append(
            "shufflevector {0} {1}\n".format(
                ", ".join(
                    "{0} {1}".format(op.type, op.get_reference())  # type: ignore
                    for op in self.operands
                ),
                self._stringify_metadata(leading_comma=True),
            )
        )


class ExtractValue(Instruction):
    def __init__(
        self,
        parent: Block,
        agg: Constant,
        indices: list[Constant],
        name: str = "",
    ) -> None:
        typ = agg.type
        try:
            for i in indices:
                typ = typ.elements[i]  # type: ignore  # literal struct type?
        except (AttributeError, IndexError):
            raise TypeError("Can't index at {!r} in {}".format(list(indices), agg.type))

        super().__init__(
            parent=parent,
            typ=typ,  # type: ignore
            opname="extractvalue",
            operands=[agg],
            name=name,
        )

        self.aggregate = agg
        self.indices = indices

    def descr(self, buf: list[str]) -> None:
        indices = [str(i) for i in self.indices]

        buf.append(
            "extractvalue {0} {1}, {2} {3}\n".format(
                self.aggregate.type,
                self.aggregate.get_reference(),
                ", ".join(indices),
                self._stringify_metadata(leading_comma=True),
            )
        )


class InsertValue(Instruction):
    def __init__(
        self,
        parent: Block,
        agg: Constant,
        elem: Constant,
        indices: list[Constant],
        name: str = "",
    ) -> None:
        typ = agg.type
        try:
            for i in indices:
                typ = typ.elements[i]  # type: ignore
        except (AttributeError, IndexError):
            raise TypeError("Can't index at {!r} in {}".format(list(indices), agg.type))
        if elem.type != typ:
            raise TypeError(
                f"Can only insert {typ} at {list(indices)!r} in {agg.type}: got {elem.type}"
            )
        super().__init__(parent, agg.type, "insertvalue", [agg, elem], name=name)

        self.aggregate = agg
        self.value = elem
        self.indices = indices

    def descr(self, buf: list[str]) -> None:
        indices = [str(i) for i in self.indices]

        buf.append(
            "insertvalue {0} {1}, {2} {3}, {4} {5}\n".format(
                self.aggregate.type,
                self.aggregate.get_reference(),
                self.value.type,
                self.value.get_reference(),
                ", ".join(indices),
                self._stringify_metadata(leading_comma=True),
            )
        )


class Unreachable(Instruction):
    def __init__(self, parent: Block) -> None:
        super().__init__(
            parent=parent,
            typ=types.VoidType(),
            opname="unreachable",
            operands=[],
            name="",
        )

    def descr(self, buf: list[str]) -> None:
        buf += (self.opname, "\n")


class InlineAsm:
    def __init__(
        self,
        ftype: types.FunctionType,
        asm: str,
        constraint: Value,
        side_effect: bool = False,
    ) -> None:
        self.type = ftype.return_type
        self.function_type = ftype
        self.asm = asm
        self.constraint = constraint
        self.side_effect = side_effect

    def descr(self, buf: list[str]) -> None:
        sideeffect = "sideeffect" if self.side_effect else ""
        fmt = 'asm {sideeffect} "{asm}", "{constraint}"\n'
        buf.append(
            fmt.format(sideeffect=sideeffect, asm=self.asm, constraint=self.constraint)
        )

    def get_reference(self) -> str:
        buf: list[str] = []
        self.descr(buf)
        return "".join(buf)

    def __str__(self) -> str:
        return "{0} {1}".format(self.type, self.get_reference())


class AtomicRMW(Instruction):
    def __init__(
        self,
        parent: Block,
        op: str,
        ptr: Constant,
        val: Constant,
        ordering: str,
        name: str,
    ) -> None:
        super().__init__(
            parent=parent,
            typ=val.type,
            opname="atomicrmw",
            operands=[ptr, val],
            name=name,
        )
        self.operation = op
        self.ordering = ordering

    def descr(self, buf: list[str]) -> None:
        ptr, val = self.operands
        fmt = "atomicrmw {op} {ptrty} {ptr}, {valty} {val} {ordering} " "{metadata}\n"
        buf.append(
            fmt.format(
                op=self.operation,
                ptrty=ptr.type,  # type: ignore
                ptr=ptr.get_reference(),  # type: ignore
                valty=val.type,  # type: ignore
                val=val.get_reference(),  # type: ignore
                ordering=self.ordering,
                metadata=self._stringify_metadata(leading_comma=True),
            )
        )


class CmpXchg(Instruction):
    """This instruction has changed since llvm3.5.  It is not compatible with
    older llvm versions.
    """

    def __init__(
        self,
        parent: Block,
        ptr: Constant,
        cmp: Constant,
        val: Constant,
        ordering: str,
        failordering: str,
        name: str,
    ) -> None:
        outtype = types.LiteralStructType([val.type, types.IntType(1)])
        super().__init__(
            parent=parent,
            typ=outtype,
            opname="cmpxchg",
            operands=[ptr, cmp, val],
            name=name,
        )
        self.ordering = ordering
        self.failordering = failordering

    def descr(self, buf: list[str]) -> None:
        ptr, cmpval, val = self.operands
        fmt = (
            "cmpxchg {ptrty} {ptr}, {ty} {cmp}, {ty} {val} {ordering} "
            "{failordering} {metadata}\n"
        )
        buf.append(
            fmt.format(
                ptrty=ptr.type,  # type: ignore
                ptr=ptr.get_reference(),  # type: ignore
                ty=cmpval.type,  # type: ignore
                cmp=cmpval.get_reference(),  # type: ignore
                val=val.get_reference(),  # type: ignore
                ordering=self.ordering,
                failordering=self.failordering,
                metadata=self._stringify_metadata(leading_comma=True),
            )
        )


class _LandingPadClause:
    def __init__(self, value: Constant) -> None:
        self.value = value
        # FIXME: does not contain self.kind

    def __str__(self) -> str:
        return "{kind} {type} {value}".format(
            kind=self.kind,  # type: ignore
            type=self.value.type,
            value=self.value.get_reference(),
        )


class CatchClause(_LandingPadClause):
    kind = "catch"


class FilterClause(_LandingPadClause):
    kind = "filter"

    def __init__(self, value: Constant) -> None:
        assert isinstance(value, Constant)
        assert isinstance(value.type, types.ArrayType)
        super().__init__(value)


class LandingPadInstr(Instruction):
    def __init__(
        self, parent: Block, typ: types.Type, name: str = "", cleanup: bool = False
    ) -> None:
        super().__init__(
            parent=parent, typ=typ, opname="landingpad", operands=[], name=name
        )
        self.cleanup = cleanup
        self.clauses: list[_LandingPadClause] = []

    def add_clause(self, clause: _LandingPadClause) -> None:
        assert isinstance(clause, _LandingPadClause)
        self.clauses.append(clause)

    def descr(self, buf: list[str]) -> None:
        fmt = "landingpad {type}{cleanup}{clauses}\n"
        buf.append(
            fmt.format(
                type=self.type,
                cleanup=" cleanup" if self.cleanup else "",
                clauses="".join(
                    ["\n      {0}".format(clause) for clause in self.clauses]
                ),
            )
        )


class Fence(Instruction):
    """
    The `fence` instruction.

    As of LLVM 5.0.1:

    fence [syncscope("<target-scope>")] <ordering>  ; yields void
    """

    VALID_FENCE_ORDERINGS = {"acquire", "release", "acq_rel", "seq_cst"}

    def __init__(
        self,
        parent: Block,
        ordering: Literal["acquire", "release", "acq_rel", "seq_cst"],
        targetscope: None = None,
        name: str = "",
    ) -> None:
        super().__init__(
            parent=parent,
            typ=types.VoidType(),
            opname="fence",
            operands=[],
            name=name,
        )
        if ordering not in self.VALID_FENCE_ORDERINGS:
            msg = 'Invalid fence ordering "{0}"! Should be one of {1}.'
            raise ValueError(
                msg.format(ordering, ", ".join(self.VALID_FENCE_ORDERINGS))
            )
        self.ordering = ordering
        self.targetscope = targetscope

    def descr(self, buf: list[str]) -> None:
        if self.targetscope is None:
            syncscope = ""
        else:
            syncscope = 'syncscope("{0}") '.format(self.targetscope)

        fmt = "fence {syncscope}{ordering}\n"
        buf.append(
            fmt.format(
                syncscope=syncscope,
                ordering=self.ordering,
            )
        )
