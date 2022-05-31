from __future__ import annotations

import contextlib
from typing import Any, ContextManager, Iterator, Sequence, cast

from typing_extensions import Literal

from llvmlite.ir import instructions, types, values
from llvmlite.ir.instructions import (
    Branch,
    CallInstr,
    CastInstr,
    Instruction,
    LandingPadInstr,
)
from llvmlite.ir.module import Module

_CMP_MAP = {
    ">": "gt",
    "<": "lt",
    "==": "eq",
    "!=": "ne",
    ">=": "ge",
    "<=": "le",
}


def _label_suffix(label: str, suffix: str) -> str:
    """Returns (label + suffix) or a truncated version if it's too long."""
    if len(label) > 50:
        nhead = 25
        return "".join([label[:nhead], "..", suffix])
    else:
        return label + suffix


class IRBuilder:
    def __init__(self, block: values.Block | None = None) -> None:
        self._block: values.Block | None = block
        self._anchor = len(block.instructions) if block else 0
        self.debug_metadata = None

    def _unop(
        self,
        opname: str,
        arg: values.Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> Instruction:
        instr = Instruction(
            self.block,
            arg.type,
            opname,
            [arg],
            name,
            flags,
        )
        self._insert(instr)
        return instr

    def _binop(
        self,
        opname: str,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[str, ...] = (),
    ) -> Instruction:
        if lhs.type != rhs.type:
            raise ValueError(
                f"Operands must be the same type, got ({lhs.type}, {rhs.type})"
            )
        instr = Instruction(
            self.block,
            lhs.type,
            opname,
            [lhs, rhs],
            name,
            flags,
        )
        self._insert(instr)
        return instr

    def _binop_with_overflow(
        self,
        opname: str,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
    ) -> Instruction:
        if lhs.type != rhs.type:
            raise ValueError(
                f"Operands must be the same type, got ({lhs.type}, {rhs.type})"
            )
        ty = lhs.type
        if not isinstance(ty, types.IntType):
            raise TypeError(f"expected an integer type, got {ty}")
        bool_ty = types.IntType(1)

        mod = self.module
        fnty = types.FunctionType(types.LiteralStructType([ty, bool_ty]), [ty, ty])
        fn = mod.declare_intrinsic(f"llvm.{opname}.with.overflow", [ty], fnty)
        # FIXME: is this cast ok?
        ret = self.call(cast(values.Function, fn), [lhs, rhs], name=name)
        return ret

    def _uniop(
        self,
        opname: str,
        operand: values.Constant,
        name: str = "",
    ) -> Instruction:
        instr = Instruction(
            self.block,
            operand.type,
            opname,
            [operand],
            name,
        )
        self._insert(instr)
        return instr

    def _uniop_intrinsic_int(
        self,
        opname: str,
        operand: values.Constant,
        name: str = "",
    ) -> Instruction:

        if not isinstance(operand.type, types.IntType):
            raise TypeError(f"expected an integer type, got {operand.type}")
        fn = self.module.declare_intrinsic(opname, [operand.type])
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [operand], name)

    def _uniop_intrinsic_float(
        self,
        opname: str,
        operand: values.Constant,
        name: str = "",
    ) -> CallInstr:
        if not isinstance(operand.type, (types.FloatType, types.DoubleType)):
            raise TypeError(f"expected a float type, got {operand.type}")
        fn = self.module.declare_intrinsic(opname, [operand.type])
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [operand], name)

    def _uniop_intrinsic_with_flag(
        self,
        opname: str,
        operand: values.Constant,
        flag: Any,
        name: str = "",
    ) -> CallInstr:
        if not isinstance(operand.type, types.IntType):
            raise TypeError(f"expected an integer type, got {operand.type}")
        if not (isinstance(flag.type, types.IntType) and flag.type.width == 1):
            raise TypeError(f"expected an i1 type, got {flag.type}")
        fn = self.module.declare_intrinsic(opname, [operand.type, flag.type])
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [operand, flag], name)

    def _triop_intrinsic(
        self,
        opname: str,
        a: values.Constant,
        b: values.Constant,
        c: values.Constant,
        name: str = "",
    ) -> CallInstr:
        if a.type != b.type or b.type != c.type:
            raise TypeError(
                f"expected types to be the same, got {a.type}, {b.type}, {c.type}"
            )
        elif not isinstance(
            a.type, (types.HalfType, types.FloatType, types.DoubleType)
        ):
            raise TypeError(f"expected an floating point type, got {a.type}")
        fn = self.module.declare_intrinsic(opname, [a.type, b.type, c.type])
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [a, b, c], name)

    def _castop(
        self,
        opname: str,
        val: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | CastInstr:
        if val.type == typ:
            return val
        instr = instructions.CastInstr(
            self.block,
            opname,
            val,
            typ,
            name,
        )
        self._insert(instr)
        return instr

    @property
    def block(self) -> values.Block:
        """
        The current basic block.
        """
        block = self._block
        if block is None:
            raise AttributeError("Block is None")
        return block

    @property
    def function(self) -> values.Function:
        """
        The current function.
        """
        # FIXME: is the cast here ok?
        return cast(values.Function, self.block.parent)

    @property
    def module(self) -> Module:
        """
        The current module.
        """
        # FIXME: is the cast here ok?
        return cast(values.Function, self.block.parent).module

    def position_before(self, instr: Instruction) -> None:
        """
        Position immediately before the given instruction.  The current block
        is also changed to the instruction's basic block.
        """
        # FIXME: is the cast here ok?
        self._block = cast(values.Block, instr.parent)
        self._anchor = self._block.instructions.index(instr)

    def position_after(self, instr: Instruction) -> None:
        """
        Position immediately after the given instruction.  The current block
        is also changed to the instruction's basic block.
        """
        # FIXME: is the cast here ok?
        self._block = cast(values.Block, instr.parent)
        self._anchor = self._block.instructions.index(instr) + 1

    def position_at_start(self, block: values.Block) -> None:
        """
        Position at the start of the basic *block*.
        """
        self._block = block
        self._anchor = 0

    def position_at_end(self, block: values.Block) -> None:
        """
        Position at the end of the basic *block*.
        """
        self._block = block
        self._anchor = len(block.instructions)

    def append_basic_block(self, name: str = "") -> values.Block:
        """
        Append a basic block, with the given optional *name*, to the current
        function.  The current block is not changed.  The new block is returned.
        """
        return self.function.append_basic_block(name)

    def remove(self, instr: Instruction) -> None:
        """Remove the given instruction."""
        # FIXME: is this cast ok?
        block = cast(values.Block, self._block)
        idx = block.instructions.index(instr)
        del block.instructions[idx]
        if block.terminator == instr:
            block.terminator = None
        if self._anchor > idx:
            self._anchor -= 1

    @contextlib.contextmanager
    def goto_block(self, block: values.Block) -> Iterator[None]:
        """
        A context manager which temporarily positions the builder at the end
        of basic block *bb* (but before any terminator).
        """
        old_block = self.block
        term = block.terminator
        if term is not None:
            self.position_before(term)
        else:
            self.position_at_end(block)
        try:
            yield
        finally:
            self.position_at_end(old_block)

    @contextlib.contextmanager
    def goto_entry_block(self) -> Iterator[None]:
        """
        A context manager which temporarily positions the builder at the
        end of the function's entry block.
        """
        with self.goto_block(self.function.entry_basic_block):
            yield

    @contextlib.contextmanager
    def _branch_helper(
        self, bbenter: values.Block, bbexit: values.Block
    ) -> Iterator[values.Block]:
        self.position_at_end(bbenter)
        yield bbexit
        if self.block.terminator is None:
            self.branch(bbexit)

    @contextlib.contextmanager
    def if_then(
        self,
        pred: values.Constant,
        likely: bool | None = None,
    ) -> Iterator[values.Block]:
        """
        A context manager which sets up a conditional basic block based
        on the given predicate (a i1 value).  If the conditional block
        is not explicitly terminated, a branch will be added to the next
        block.
        If *likely* is given, its boolean value indicates whether the
        predicate is likely to be true or not, and metadata is issued
        for LLVM's optimizers to account for that.
        """
        bb = self.block
        bbif = self.append_basic_block(name=_label_suffix(bb.name, ".if"))
        bbend = self.append_basic_block(name=_label_suffix(bb.name, ".endif"))
        br = self.cbranch(pred, bbif, bbend)
        if likely is not None:
            br.set_weights([99, 1] if likely else [1, 99])

        with self._branch_helper(bbif, bbend):
            yield bbend

        self.position_at_end(bbend)

    @contextlib.contextmanager
    def if_else(
        self, pred: values.Constant, likely: bool | None = None
    ) -> Iterator[tuple[ContextManager[values.Block], ContextManager[values.Block]]]:
        """
        A context manager which sets up two conditional basic blocks based
        on the given predicate (a i1 value).
        A tuple of context managers is yield'ed.  Each context manager
        acts as a if_then() block.
        *likely* has the same meaning as in if_then().

        Typical use::
            with builder.if_else(pred) as (then, otherwise):
                with then:
                    # emit instructions for when the predicate is true
                with otherwise:
                    # emit instructions for when the predicate is false
        """
        bb = self.block
        if bb is None:
            raise AttributeError("No basic block set")
        bbif = self.append_basic_block(name=_label_suffix(bb.name, ".if"))
        bbelse = self.append_basic_block(name=_label_suffix(bb.name, ".else"))
        bbend = self.append_basic_block(name=_label_suffix(bb.name, ".endif"))
        br = self.cbranch(pred, bbif, bbelse)
        if likely is not None:
            br.set_weights([99, 1] if likely else [1, 99])

        then = self._branch_helper(bbif, bbend)
        otherwise = self._branch_helper(bbelse, bbend)

        yield then, otherwise

        self.position_at_end(bbend)

    def _insert(self, instr: Instruction) -> None:
        if self.debug_metadata is not None and "dbg" not in instr.metadata:
            instr.metadata["dbg"] = self.debug_metadata
        # FIXME: is this cast ok?
        cast(values.Block, self._block).instructions.insert(self._anchor, instr)
        self._anchor += 1

    def _set_terminator(self, term: Instruction) -> Instruction:
        assert not self.block.is_terminated
        self._insert(term)
        self.block.terminator = term
        return term

    #
    # Arithmetic APIs
    #

    def shl(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Left integer shift:
            name = lhs << rhs
        """
        return self._binop("shl", lhs, rhs, name)

    def lshr(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Logical (unsigned) right integer shift:
            name = lhs >> rhs
        """
        return self._binop("lshr", lhs, rhs, name)

    def ashr(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Arithmetic (signed) right integer shift:
            name = lhs >> rhs
        """
        return self._binop("ashr", lhs, rhs, name)

    def add(
        self,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[str, ...] = (),
    ) -> instructions.Instruction:
        """
        Integer addition:
            name = lhs + rhs
        """
        return self._binop("add", lhs, rhs, name, flags)

    def fadd(
        self,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[str, ...] = (),
    ) -> instructions.Instruction:
        """
        Floating-point addition:
            name = lhs + rhs
        """
        return self._binop("fadd", lhs, rhs, name, flags)

    def sub(
        self,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[str, ...] = (),
    ) -> instructions.Instruction:
        """
        Integer subtraction:
            name = lhs - rhs
        """
        return self._binop("sub", lhs, rhs, name, flags)

    def fsub(
        self,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[str, ...] = (),
    ) -> instructions.Instruction:
        """
        Floating-point subtraction:
            name = lhs - rhs
        """
        return self._binop("fsub", lhs, rhs, name, flags)

    def mul(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Integer multiplication:
            name = lhs * rhs
        """
        return self._binop("mul", lhs, rhs, name)

    def fmul(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Floating-point multiplication:
            name = lhs * rhs
        """
        return self._binop("fmul", lhs, rhs, name)

    def udiv(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Unsigned integer division:
            name = lhs / rhs
        """
        return self._binop("udiv", lhs, rhs, name)

    def sdiv(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Signed integer division:
            name = lhs / rhs
        """
        return self._binop("sdiv", lhs, rhs, name)

    def fdiv(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Floating-point division:
            name = lhs / rhs
        """
        return self._binop("fdiv", lhs, rhs, name)

    def urem(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Unsigned integer remainder:
            name = lhs % rhs
        """
        return self._binop("urem", lhs, rhs, name)

    def srem(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Signed integer remainder:
            name = lhs % rhs
        """
        return self._binop("srem", lhs, rhs, name)

    def frem(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Floating-point remainder:
            name = lhs % rhs
        """
        return self._binop("frem", lhs, rhs, name)

    def or_(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Bitwise integer OR:
            name = lhs | rhs
        """
        return self._binop("or", lhs, rhs, name)

    def and_(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Bitwise integer AND:
            name = lhs & rhs
        """
        return self._binop("and", lhs, rhs, name)

    def xor(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Bitwise integer XOR:
            name = lhs ^ rhs
        """
        return self._binop("xor", lhs, rhs, name)

    def sadd_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Signed integer addition with overflow:
            name = {result, overflow bit} = lhs + rhs
        """
        return self._binop_with_overflow("sadd", lhs, rhs, name)

    def smul_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Signed integer multiplication with overflow:
            name = {result, overflow bit} = lhs * rhs
        """
        return self._binop_with_overflow("smul", lhs, rhs, name)

    def ssub_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Signed integer subtraction with overflow:
            name = {result, overflow bit} = lhs - rhs
        """
        return self._binop_with_overflow("ssub", lhs, rhs, name)

    def uadd_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Unsigned integer addition with overflow:
            name = {result, overflow bit} = lhs + rhs
        """
        return self._binop_with_overflow("uadd", lhs, rhs, name)

    def umul_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Unsigned integer multiplication with overflow:
            name = {result, overflow bit} = lhs * rhs
        """
        return self._binop_with_overflow("umul", lhs, rhs, name)

    def usub_with_overflow(
        self, lhs: values.Constant, rhs: values.Constant, name: str = ""
    ) -> instructions.Instruction:
        """
        Unsigned integer subtraction with overflow:
            name = {result, overflow bit} = lhs - rhs
        """
        return self._binop_with_overflow("usub", lhs, rhs, name)

    #
    # Unary APIs
    #

    def not_(
        self,
        value: values.Constant,
        name: str = "",
    ) -> instructions.Instruction:
        """
        Bitwise integer complement:
            name = ~value
        """
        if isinstance(value.type, types.VectorType):
            rhs = values.Constant(value.type, (-1,) * value.type.count)
        else:
            rhs = values.Constant(value.type, -1)
        return self.xor(value, rhs, name=name)

    def neg(
        self,
        value: values.Constant,
        name: str = "",
    ) -> instructions.Instruction:
        """
        Integer negative:
            name = -value
        """
        return self.sub(values.Constant(value.type, 0), value, name=name)

    def fneg(
        self,
        arg: values.Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> instructions.Instruction:
        """
        Floating-point negative:
            name = -arg
        """
        return self._unop("fneg", arg, name, flags)

    #
    # Comparison APIs
    #

    def _icmp(
        self,
        prefix: str,
        cmpop: Literal["==", "!=", "<", "<=", ">", ">="],
        lhs: values.Constant,
        rhs: values.Constant,
        name: str,
    ) -> instructions.ICMPInstr:
        try:
            op = _CMP_MAP[cmpop]
        except KeyError:
            raise ValueError(f"invalid comparison {cmpop!r} for icmp")
        if cmpop not in ("==", "!="):
            op = prefix + op
        instr = instructions.ICMPInstr(self.block, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def icmp_signed(
        self,
        cmpop: Literal["==", "!=", "<", "<=", ">", ">="],
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
    ) -> instructions.ICMPInstr:
        """
        Signed integer comparison:
            name = lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._icmp("s", cmpop, lhs, rhs, name)

    def icmp_unsigned(
        self,
        cmpop: Literal["==", "!=", "<", "<=", ">", ">="],
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
    ) -> instructions.ICMPInstr:
        """
        Unsigned integer (or pointer) comparison:
            name = lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._icmp("u", cmpop, lhs, rhs, name)

    def fcmp_ordered(
        self,
        cmpop: Literal["==", "!=", "<", "<=", ">", ">=", "ord", "uno"],
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> instructions.FCMPInstr:
        """
        Floating-point ordered comparison:
            name = lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        if cmpop in _CMP_MAP:
            op = "o" + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(
            self.block,
            op,
            lhs,
            rhs,
            name=name,
            flags=list(flags),
        )
        self._insert(instr)
        return instr

    def fcmp_unordered(
        self,
        cmpop: Literal["==", "!=", "<", "<=", ">", ">=", "ord", "uno"],
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> instructions.FCMPInstr:
        """
        Floating-point unordered comparison:
            name = lhs <cmpop> rhs

        where cmpop can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        if cmpop in _CMP_MAP:
            op = "u" + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(
            self.block,
            op,
            lhs,
            rhs,
            name=name,
            flags=list(flags),
        )
        self._insert(instr)
        return instr

    def select(
        self,
        cond: values.Constant,
        lhs: values.Constant,
        rhs: values.Constant,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> instructions.SelectInstr:
        """
        Ternary select operator:
            name = cond ? lhs : rhs
        """
        instr = instructions.SelectInstr(
            self.block,
            cond,
            lhs,
            rhs,
            name=name,
            flags=flags,
        )
        self._insert(instr)
        return instr

    #
    # Cast APIs
    #

    def trunc(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Truncating integer downcast to a smaller type:
            name = (typ) value
        """
        return self._castop("trunc", value, typ, name)

    def zext(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Zero-extending integer upcast to a larger type:
            name = (typ) value
        """
        return self._castop("zext", value, typ, name)

    def sext(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Sign-extending integer upcast to a larger type:
            name = (typ) value
        """
        return self._castop("sext", value, typ, name)

    def fptrunc(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Floating-point downcast to a less precise type:
            name = (typ) value
        """
        return self._castop("fptrunc", value, typ, name)

    def fpext(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Floating-point upcast to a more precise type:
            name = (typ) value
        """
        return self._castop("fpext", value, typ, name)

    def bitcast(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Pointer cast to a different pointer type:
            name = (typ) value
        """
        return self._castop("bitcast", value, typ, name)

    def addrspacecast(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Pointer cast to a different address space:
            name = (typ) value
        """
        return self._castop("addrspacecast", value, typ, name)

    def fptoui(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Convert floating-point to unsigned integer:
            name = (typ) value
        """
        return self._castop("fptoui", value, typ, name)

    def uitofp(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Convert unsigned integer to floating-point:
            name = (typ) value
        """
        return self._castop("uitofp", value, typ, name)

    def fptosi(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Convert floating-point to signed integer:
            name = (typ) value
        """
        return self._castop("fptosi", value, typ, name)

    def sitofp(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Convert signed integer to floating-point:
            name = (typ) value
        """
        return self._castop("sitofp", value, typ, name)

    def ptrtoint(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Cast pointer to integer:
            name = (typ) value
        """
        return self._castop("ptrtoint", value, typ, name)

    def inttoptr(
        self,
        value: values.Constant,
        typ: types.Type,
        name: str = "",
    ) -> values.Constant | instructions.CastInstr:
        """
        Cast integer to pointer:
            name = (typ) value
        """
        return self._castop("inttoptr", value, typ, name)

    #
    # Memory APIs
    #

    def alloca(
        self,
        typ: types.Type,
        size: values.Value | None = None,
        name: str = "",
    ) -> instructions.AllocaInstr:
        """
        Stack-allocate a slot for *size* elements of the given type.
        (default one element)
        """
        # FIXME: values.Value has no .type
        if size is None:
            pass
        elif isinstance(size, (values.Value, values.Constant)):
            assert isinstance(size.type, types.IntType)  # type: ignore
        else:
            # If it is not a Value instance,
            # assume to be a Python integer.
            size = values.Constant(types.IntType(32), size)

        al = instructions.AllocaInstr(
            self.block,
            typ,
            size,
            name,
        )
        self._insert(al)
        return al

    def load(
        self,
        ptr: values.Value,
        name: str = "",
        align: int | None = None,
    ) -> instructions.LoadInstr:
        """
        Load value from pointer, with optional guaranteed alignment:
            name = *ptr
        """
        # FIXME: values.Value has no .type
        if not isinstance(ptr.type, types.PointerType):  # type: ignore
            raise TypeError(
                f"cannot load from value of type {ptr.type} "  # type: ignore
                f"({str(ptr)!r}): not a pointer"
            )
        ld = instructions.LoadInstr(
            self.block,
            ptr,
            name,
        )
        ld.align = align
        self._insert(ld)
        return ld

    def store(
        self,
        value: values.Value,
        ptr: values.Value,
        align: int | None = None,
    ) -> instructions.StoreInstr:
        """
        Store value to pointer, with optional guaranteed alignment:
            *ptr = name
        """
        # FIXME: values.Value has no .type
        if not isinstance(ptr.type, types.PointerType):  # type: ignore
            raise TypeError(
                f"cannot store to value of type {ptr.type} "  # type: ignore
                f"({str(ptr)!r}): not a pointer"
            )
        if ptr.type.pointee != value.type:  # type: ignore
            raise TypeError(
                f"cannot store {value.type} to "  # type: ignore
                f"{ptr.type}: mismatching types"  # type: ignore
            )
        st = instructions.StoreInstr(
            self.block,
            value,
            ptr,
        )
        st.align = align
        self._insert(st)
        return st

    def load_atomic(
        self,
        ptr: values.Value,
        ordering: str,  # FIXME: Literal["seq_cst"] and which others?
        align: int,
        name: str = "",
    ) -> instructions.LoadAtomicInstr:
        """
        Load value from pointer, with optional guaranteed alignment:
            name = *ptr
        """
        # FIXME: values.Value has no .type
        if not isinstance(ptr.type, types.PointerType):  # type: ignore
            raise TypeError(
                f"cannot load from value of type {ptr.type} ({str(ptr)!r}): not a pointer"  # type: ignore
            )
        ld = instructions.LoadAtomicInstr(
            self.block,
            ptr,
            ordering,
            align,
            name,
        )
        self._insert(ld)
        return ld

    def store_atomic(
        self,
        value: values.Value,
        ptr: values.Value,
        ordering: str,  # FIXME: Literal["seq_cst"] and which others?
        align: int,
    ) -> instructions.StoreAtomicInstr:
        """
        Store value to pointer, with optional guaranteed alignment:
            *ptr = name
        """
        # FIXME: values.Value has no .type
        if not isinstance(ptr.type, types.PointerType):  # type: ignore
            msg = "cannot store to value of type {} ({!r}): not a pointer"
            raise TypeError(msg.format(ptr.type, str(ptr)))  # type: ignore
        if ptr.type.pointee != value.type:  # type: ignore
            raise TypeError(
                "cannot store {} to {}: mismatching types".format(value.type, ptr.type)  # type: ignore
            )
        st = instructions.StoreAtomicInstr(
            self.block,
            value,
            ptr,
            ordering,
            align,
        )
        self._insert(st)
        return st

    #
    # Terminators APIs
    #

    def switch(self, value: values.Value, default: Any) -> instructions.SwitchInstr:
        """
        Create a switch-case with a single *default* target.
        """
        swt = instructions.SwitchInstr(
            self.block,
            "switch",
            value,
            default,
        )
        self._set_terminator(swt)
        return swt

    def branch(self, target: values.Block) -> Branch:
        """
        Unconditional branch to *target*.
        """
        br = Branch(self.block, "br", [target])
        self._set_terminator(br)
        return br

    def cbranch(
        self,
        cond: values.Constant,
        truebr: values.Block,
        falsebr: values.Block,
    ) -> instructions.ConditionalBranch:
        """
        Conditional branch to *truebr* if *cond* is true, else to *falsebr*.
        """
        br = instructions.ConditionalBranch(self.block, "br", [cond, truebr, falsebr])
        self._set_terminator(br)
        return br

    def branch_indirect(self, addr: values.Block) -> instructions.IndirectBranch:
        """
        Indirect branch to target *addr*.
        """
        br = instructions.IndirectBranch(self.block, "indirectbr", addr)
        self._set_terminator(br)
        return br

    def ret_void(self) -> instructions.Instruction:
        """
        Return from function without a value.
        """
        return self._set_terminator(instructions.Ret(self.block, "ret void"))

    def ret(self, value: values.Value) -> instructions.Instruction:
        """
        Return from function with the given *value*.
        """
        return self._set_terminator(instructions.Ret(self.block, "ret", value))

    def resume(self, landingpad: LandingPadInstr) -> Branch:
        """
        Resume an in-flight exception.
        """
        br = Branch(self.block, "resume", [landingpad])
        self._set_terminator(br)
        return br

    # Call APIs

    def call(
        self,
        fn: values.Function | instructions.InlineAsm,
        args: Sequence[values.Constant],
        name: str = "",
        cconv: None = None,
        tail: bool = False,
        fastmath: tuple[Any, ...] = (),
        attrs: tuple[Any, ...] = (),
        arg_attrs: None = None,
    ) -> instructions.CallInstr:
        """
        Call function *fn* with *args*:
            name = fn(args...)
        """
        inst = instructions.CallInstr(
            self.block,
            fn,
            args,
            name=name,
            cconv=cconv,
            tail=tail,
            fastmath=fastmath,
            attrs=attrs,
            arg_attrs=arg_attrs,
        )
        self._insert(inst)
        return inst

    def asm(
        self,
        ftype: types.FunctionType,
        asm: str,
        constraint: Any,
        args: Sequence[values.Constant],
        side_effect: bool,
        name: str = "",
    ) -> CallInstr:
        """
        Inline assembler.
        """
        asm_instr = instructions.InlineAsm(ftype, asm, constraint, side_effect)
        return self.call(asm_instr, args, name)

    def load_reg(
        self,
        reg_type: types.Type,
        reg_name: str,
        name: str = "",
    ) -> CallInstr:
        """
        Load a register value into an LLVM value.
          Example: v = load_reg(IntType(32), "eax")
        """
        ftype = types.FunctionType(reg_type, [])
        return self.asm(ftype, "", "={{{}}}".format(reg_name), [], False, name)

    def store_reg(
        self,
        value: values.Constant,
        reg_type: types.Type,
        reg_name: str,
        name: str = "",
    ) -> CallInstr:
        """
        Store an LLVM value inside a register
        Example:
          store_reg(Constant(IntType(32), 0xAAAAAAAA), IntType(32), "eax")
        """
        ftype = types.FunctionType(types.VoidType(), [reg_type])
        return self.asm(ftype, "", "{{{}}}".format(reg_name), [value], True, name)

    def invoke(
        self,
        fn: values.Function,
        args: Sequence[values.Constant],
        normal_to: values.Block,
        unwind_to: values.Block,
        name: str = "",
        cconv: str | None = None,
        fastmath: tuple[str, ...] = (),
        attrs: tuple[str, ...] = (),
        arg_attrs: dict[int, tuple[Any, ...]] | None = None,
    ) -> instructions.InvokeInstr:
        inst = instructions.InvokeInstr(
            self.block,
            fn,
            args,
            normal_to,
            unwind_to,
            name=name,
            cconv=cconv,
            fastmath=fastmath,
            attrs=attrs,
            arg_attrs=arg_attrs,
        )
        self._set_terminator(inst)
        return inst

    # GEP APIs

    def gep(
        self,
        ptr: values.Constant,
        indices: list[values.Constant],
        inbounds: bool = False,
        name: str = "",
    ) -> instructions.GEPInstr:
        """
        Compute effective address (getelementptr):
            name = getelementptr ptr, <indices...>
        """
        instr = instructions.GEPInstr(
            self.block,
            ptr,
            indices,
            inbounds=inbounds,
            name=name,
        )
        self._insert(instr)
        return instr

    # Vector Operations APIs

    def extract_element(
        self,
        vector: values.Constant,
        idx: values.Constant,
        name: str = "",
    ) -> instructions.ExtractElement:
        """
        Returns the value at position idx.
        """
        instr = instructions.ExtractElement(self.block, vector, idx, name=name)
        self._insert(instr)
        return instr

    def insert_element(
        self,
        vector: values.Constant,
        value: values.Constant,
        idx: values.Constant,
        name: str = "",
    ) -> instructions.InsertElement:
        """
        Returns vector with vector[idx] replaced by value.
        The result is undefined if the idx is larger or equal the vector length.
        """
        instr = instructions.InsertElement(self.block, vector, value, idx, name=name)
        self._insert(instr)
        return instr

    def shuffle_vector(
        self,
        vector1: values.Constant,
        vector2: values.Constant,
        mask: values.Constant,
        name: str = "",
    ) -> instructions.ShuffleVector:
        """
        Constructs a permutation of elements from *vector1* and *vector2*.
        Returns a new vector in the same length of *mask*.

        * *vector1* and *vector2* must have the same element type.
        * *mask* must be a constant vector of integer types.
        """
        instr = instructions.ShuffleVector(
            self.block, vector1, vector2, mask, name=name
        )
        self._insert(instr)
        return instr

    # Aggregate APIs

    def extract_value(
        self,
        agg: values.Constant,
        idx: values.Constant | list[values.Constant],
        name: str = "",
    ) -> instructions.ExtractValue:
        """
        Extract member number *idx* from aggregate.
        """
        if not isinstance(idx, (tuple, list)):
            idx = [idx]
        instr = instructions.ExtractValue(self.block, agg, idx, name=name)
        self._insert(instr)
        return instr

    def insert_value(
        self,
        agg: values.Constant,
        value: values.Constant,
        idx: values.Constant | list[values.Constant],
        name: str = "",
    ) -> instructions.InsertValue:
        """
        Insert *value* into member number *idx* from aggregate.
        """
        if not isinstance(idx, (tuple, list)):
            idx = [idx]
        instr = instructions.InsertValue(self.block, agg, value, idx, name=name)
        self._insert(instr)
        return instr

    # PHI APIs

    def phi(
        self,
        typ: types.Type,
        name: str = "",
        flags: tuple[Any, ...] = (),
    ) -> instructions.PhiInstr:
        inst = instructions.PhiInstr(self.block, typ, name=name, flags=flags)
        self._insert(inst)
        return inst

    # Special API

    def unreachable(self) -> instructions.Unreachable:
        inst = instructions.Unreachable(self.block)
        self._set_terminator(inst)
        return inst

    def atomic_rmw(
        self,
        op: str,
        ptr: values.Constant,
        val: values.Constant,
        ordering: str,
        name: str = "",
    ) -> instructions.AtomicRMW:
        inst = instructions.AtomicRMW(self.block, op, ptr, val, ordering, name=name)
        self._insert(inst)
        return inst

    def cmpxchg(
        self,
        ptr: values.Constant,
        cmp: values.Constant,
        val: values.Constant,
        ordering: str,
        failordering: str | None = None,
        name: str = "",
    ) -> instructions.CmpXchg:
        """
        Atomic compared-and-set:
            atomic {
                old = *ptr
                success = (old == cmp)
                if (success)
                    *ptr = val
                }
            name = { old, success }

        If failordering is `None`, the value of `ordering` is used.
        """
        failordering = ordering if failordering is None else failordering
        inst = instructions.CmpXchg(
            self.block,
            ptr,
            cmp,
            val,
            ordering,
            failordering,
            name=name,
        )
        self._insert(inst)
        return inst

    def landingpad(
        self,
        typ: types.Type,
        name: str = "",
        cleanup: bool = False,
    ) -> instructions.LandingPadInstr:
        inst = instructions.LandingPadInstr(self.block, typ, name, cleanup)
        self._insert(inst)
        return inst

    def assume(self, cond: values.Constant) -> CallInstr:
        """
        Optimizer hint: assume *cond* is always true.
        """
        fn = self.module.declare_intrinsic("llvm.assume")
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [cond])

    def fence(
        self,
        ordering: Literal["acquire", "release", "acq_rel", "seq_cst"],
        targetscope: None = None,
        name: str = "",
    ) -> instructions.Fence:
        """
        Add a memory barrier, preventing certain reorderings of load and/or
        store accesses with
        respect to other processors and devices.
        """
        inst = instructions.Fence(self.block, ordering, targetscope, name=name)
        self._insert(inst)
        return inst

    def bswap(self, cond: values.Constant, name: str = "") -> Instruction:
        """
        Used to byte swap integer values with an even number of bytes (positive
        multiple of 16 bits)
        """
        return self._uniop_intrinsic_int("llvm.bswap", cond, name)

    def bitreverse(self, cond: values.Constant, name: str = "") -> Instruction:
        """
        Reverse the bitpattern of an integer value; for example 0b10110110
        becomes 0b01101101.
        """
        return self._uniop_intrinsic_int("llvm.bitreverse", cond, name)

    def ctpop(self, cond: values.Constant, name: str = "") -> Instruction:
        """
        Counts the number of bits set in a value.
        """
        return self._uniop_intrinsic_int("llvm.ctpop", cond, name)

    def ctlz(self, cond: values.Constant, flag: bool, name: str = "") -> Instruction:
        """
        Counts leading zero bits in *value*. Boolean *flag* indicates whether
        the result is defined for ``0``.
        """
        return self._uniop_intrinsic_with_flag("llvm.ctlz", cond, flag, name)

    def cttz(self, cond: values.Constant, flag: bool, name: str = "") -> Instruction:
        """
        Counts trailing zero bits in *value*. Boolean *flag* indicates whether
        the result is defined for ``0``.
        """
        return self._uniop_intrinsic_with_flag("llvm.cttz", cond, flag, name)

    def fma(
        self, a: values.Constant, b: values.Constant, c: values.Constant, name: str = ""
    ) -> Instruction:
        """
        Perform the fused multiply-add operation.
        """
        return self._triop_intrinsic("llvm.fma", a, b, c, name)

    def convert_from_fp16(
        self,
        a: values.Constant,
        to: values.Constant | None = None,
        name: str = "",
    ) -> CallInstr:
        """
        Convert from an i16 to the given FP type
        """
        if not to:
            raise TypeError("expected a float return type")
        if not isinstance(to, (types.FloatType, types.DoubleType)):
            raise TypeError("expected a float type, got {}".format(to))
        if not (isinstance(a.type, types.IntType) and a.type.width == 16):
            raise TypeError("expected an i16 type, got {}".format(a.type))

        opname = "llvm.convert.from.fp16"
        fn = self.module.declare_intrinsic(opname, [to])
        # FIXME: is the cast here ok?
        return self.call(cast(values.Function, fn), [a], name)

    def convert_to_fp16(self, a: values.Constant, name: str = "") -> Instruction:
        """
        Convert the given FP number to an i16
        """
        return self._uniop_intrinsic_float("llvm.convert.to.fp16", a, name)
