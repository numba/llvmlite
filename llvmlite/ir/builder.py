from __future__ import print_function, absolute_import

import contextlib
import functools

from . import instructions, types, values

_CMP_MAP = {
    '>': 'gt',
    '<': 'lt',
    '==': 'eq',
    '!=': 'ne',
    '>=': 'ge',
    '<=': 'le',
}


def _binop(opname, cls=instructions.Instruction):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, lhs, rhs, name='', flags=()):
            if lhs.type != rhs.type:
                raise ValueError("Operands must be the same type, got (%s, %s)"
                                 % (lhs.type, rhs.type))
            instr = cls(self.block, lhs.type, opname, (lhs, rhs), name, flags)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


def _binop_with_overflow(opname, cls=instructions.Instruction):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, lhs, rhs, name=''):
            if lhs.type != rhs.type:
                raise ValueError("Operands must be the same type, got (%s, %s)"
                                 % (lhs.type, rhs.type))
            ty = lhs.type
            if not isinstance(ty, types.IntType):
                raise TypeError("expected an integer type, got %s" % (ty,))
            bool_ty = types.IntType(1)

            mod = self.module
            fnty = types.FunctionType(types.LiteralStructType([ty, bool_ty]),
                                      [ty, ty])
            fn = mod.declare_intrinsic("llvm.%s.with.overflow" % (opname,),
                                       [ty], fnty)
            ret = self.call(fn, [lhs, rhs], name=name)
            return ret

        return wrapped

    return wrap


def _uniop(opname, cls=instructions.Instruction):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, operand, name=''):
            instr = cls(self.block, operand.type, opname, [operand], name)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


def _castop(opname, cls=instructions.CastInstr):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, val, typ, name=''):
            if val.type == typ:
                return val
            instr = cls(self.block, opname, val, typ, name)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


class IRBuilder(object):
    def __init__(self, block=None):
        self._block = block
        self._anchor = len(block.instructions) if block else 0
        self.debug_metadata = None

    @property
    def block(self):
        """
        The current basic block.
        """
        return self._block

    basic_block = block

    @property
    def function(self):
        """
        The current function.
        """
        return self.block.parent

    @property
    def module(self):
        """
        The current module.
        """
        return self.block.parent.module

    def position_before(self, instr):
        """
        Position immediately before the given instruction.  The current block
        is also changed to the instruction's basic block.
        """
        self._block = instr.parent
        self._anchor = self._block.instructions.index(instr)

    def position_after(self, instr):
        """
        Position immediately after the given instruction.  The current block
        is also changed to the instruction's basic block.
        """
        self._block = instr.parent
        self._anchor = self._block.instructions.index(instr) + 1

    def position_at_start(self, block):
        """
        Position at the start of the basic *block*.
        """
        self._block = block
        self._anchor = 0

    def position_at_end(self, block):
        """
        Position at the end of the basic *block*.
        """
        self._block = block
        self._anchor = len(block.instructions)

    def append_basic_block(self, name=''):
        """
        Append a basic block, with the given optional *name*, to the current
        function.  The current block is not changed.  The new block is returned.
        """
        return self.function.append_basic_block(name)

    @contextlib.contextmanager
    def goto_block(self, block):
        """
        A context manager which temporarily positions the builder at the end
        of basic block *bb* (but before any terminator).
        """
        old_block = self.basic_block
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
    def goto_entry_block(self):
        """
        A context manager which temporarily positions the builder at the
        end of the function's entry block.
        """
        with self.goto_block(self.function.entry_basic_block):
            yield

    @contextlib.contextmanager
    def _branch_helper(self, bbenter, bbexit):
        self.position_at_end(bbenter)
        yield bbexit
        if self.basic_block.terminator is None:
            self.branch(bbexit)

    @contextlib.contextmanager
    def if_then(self, pred, likely=None):
        """
        A context manager which sets up a conditional basic block based
        on the given predicate (a i1 value).  If the conditional block
        is not explicitly terminated, a branch will be added to the next
        block.
        If *likely* is given, its boolean value indicates whether the
        predicate is likely to be true or not, and metadata is issued
        for LLVM's optimizers to account for that.
        """
        bb = self.basic_block
        bbif = self.append_basic_block(name=bb.name + '.if')
        bbend = self.append_basic_block(name=bb.name + '.endif')
        br = self.cbranch(pred, bbif, bbend)
        if likely is not None:
            br.set_weights([99, 1] if likely else [1, 99])

        with self._branch_helper(bbif, bbend):
            yield bbend

        self.position_at_end(bbend)

    @contextlib.contextmanager
    def if_else(self, pred, likely=None):
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
        bb = self.basic_block
        bbif = self.append_basic_block(name=bb.name + '.if')
        bbelse = self.append_basic_block(name=bb.name + '.else')
        bbend = self.append_basic_block(name=bb.name + '.endif')
        br = self.cbranch(pred, bbif, bbelse)
        if likely is not None:
            br.set_weights([99, 1] if likely else [1, 99])

        then = self._branch_helper(bbif, bbend)
        otherwise = self._branch_helper(bbelse, bbend)

        yield then, otherwise

        self.position_at_end(bbend)

    def _insert(self, instr):
        if self.debug_metadata is not None and 'dbg' not in instr.metadata:
            instr.metadata['dbg'] = self.debug_metadata
        self._block.instructions.insert(self._anchor, instr)
        self._anchor += 1

    def _set_terminator(self, term):
        assert not self.block.is_terminated
        self._insert(term)
        self.block.terminator = term
        return term

    #
    # Arithmetic APIs
    #

    @_binop('shl')
    def shl(self, lhs, rhs, name=''):
        """
        Left integer shift:
            name = lhs << rhs
        """

    @_binop('lshr')
    def lshr(self, lhs, rhs, name=''):
        """
        Logical (unsigned) right integer shift:
            name = lhs >> rhs
        """

    @_binop('ashr')
    def ashr(self, lhs, rhs, name=''):
        """
        Arithmetic (signed) right integer shift:
            name = lhs >> rhs
        """

    @_binop('add')
    def add(self, lhs, rhs, name=''):
        """
        Integer addition:
            name = lhs + rhs
        """

    @_binop('fadd')
    def fadd(self, lhs, rhs, name=''):
        """
        Floating-point addition:
            name = lhs + rhs
        """

    @_binop('sub')
    def sub(self, lhs, rhs, name=''):
        """
        Integer subtraction:
            name = lhs - rhs
        """

    @_binop('fsub')
    def fsub(self, lhs, rhs, name=''):
        """
        Floating-point subtraction:
            name = lhs - rhs
        """

    @_binop('mul')
    def mul(self, lhs, rhs, name=''):
        """
        Integer multiplication:
            name = lhs * rhs
        """

    @_binop('fmul')
    def fmul(self, lhs, rhs, name=''):
        """
        Floating-point multiplication:
            name = lhs * rhs
        """

    @_binop('udiv')
    def udiv(self, lhs, rhs, name=''):
        """
        Unsigned integer division:
            name = lhs / rhs
        """

    @_binop('sdiv')
    def sdiv(self, lhs, rhs, name=''):
        """
        Signed integer division:
            name = lhs / rhs
        """

    @_binop('fdiv')
    def fdiv(self, lhs, rhs, name=''):
        """
        Floating-point division:
            name = lhs / rhs
        """

    @_binop('urem')
    def urem(self, lhs, rhs, name=''):
        """
        Unsigned integer remainder:
            name = lhs % rhs
        """

    @_binop('srem')
    def srem(self, lhs, rhs, name=''):
        """
        Signed integer remainder:
            name = lhs % rhs
        """

    @_binop('frem')
    def frem(self, lhs, rhs, name=''):
        """
        Floating-point remainder:
            name = lhs % rhs
        """

    @_binop('or')
    def or_(self, lhs, rhs, name=''):
        """
        Bitwise integer OR:
            name = lhs | rhs
        """

    @_binop('and')
    def and_(self, lhs, rhs, name=''):
        """
        Bitwise integer AND:
            name = lhs & rhs
        """

    @_binop('xor')
    def xor(self, lhs, rhs, name=''):
        """
        Bitwise integer XOR:
            name = lhs ^ rhs
        """

    @_binop_with_overflow('sadd')
    def sadd_with_overflow(self, lhs, rhs, name=''):
        """
        Signed integer addition with overflow:
            name = {result, overflow bit} = lhs + rhs
        """

    @_binop_with_overflow('smul')
    def smul_with_overflow(self, lhs, rhs, name=''):
        """
        Signed integer multiplication with overflow:
            name = {result, overflow bit} = lhs * rhs
        """

    @_binop_with_overflow('ssub')
    def ssub_with_overflow(self, lhs, rhs, name=''):
        """
        Signed integer subtraction with overflow:
            name = {result, overflow bit} = lhs - rhs
        """

    @_binop_with_overflow('uadd')
    def uadd_with_overflow(self, lhs, rhs, name=''):
        """
        Unsigned integer addition with overflow:
            name = {result, overflow bit} = lhs + rhs
        """

    @_binop_with_overflow('umul')
    def umul_with_overflow(self, lhs, rhs, name=''):
        """
        Unsigned integer multiplication with overflow:
            name = {result, overflow bit} = lhs * rhs
        """

    @_binop_with_overflow('usub')
    def usub_with_overflow(self, lhs, rhs, name=''):
        """
        Unsigned integer subtraction with overflow:
            name = {result, overflow bit} = lhs - rhs
        """

    #
    # Unary APIs
    #

    def not_(self, value, name=''):
        """
        Bitwise integer complement:
            name = ~value
        """
        return self.xor(value, values.Constant(value.type, -1), name=name)

    def neg(self, value, name=''):
        """
        Integer negative:
            name = -value
        """
        return self.sub(values.Constant(value.type, 0), value, name=name)

    #
    # Comparison APIs
    #

    def _icmp(self, prefix, cmpop, lhs, rhs, name):
        try:
            op = _CMP_MAP[cmpop]
        except KeyError:
            raise ValueError("invalid comparison %r for icmp" % (cmpop,))
        if cmpop not in ('==', '!='):
            op = prefix + op
        instr = instructions.ICMPInstr(self.block, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def icmp_signed(self, cmpop, lhs, rhs, name=''):
        """
        Signed integer comparison:
            name = lhs <cmpop> rhs

        where lhs can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._icmp('s', cmpop, lhs, rhs, name)

    def icmp_unsigned(self, cmpop, lhs, rhs, name=''):
        """
        Unsigned integer (or pointer) comparison:
            name = lhs <cmpop> rhs

        where lhs can be '==', '!=', '<', '<=', '>', '>='
        """
        return self._icmp('u', cmpop, lhs, rhs, name)

    def fcmp_ordered(self, cmpop, lhs, rhs, name='', flags=[]):
        """
        Floating-point ordered comparison:
            name = lhs <cmpop> rhs

        where lhs can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        if cmpop in _CMP_MAP:
            op = 'o' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(self.block, op, lhs, rhs, name=name, flags=flags)
        self._insert(instr)
        return instr

    def fcmp_unordered(self, cmpop, lhs, rhs, name='', flags=[]):
        """
        Floating-point unordered comparison:
            name = lhs <cmpop> rhs

        where lhs can be '==', '!=', '<', '<=', '>', '>=', 'ord', 'uno'
        """
        if cmpop in _CMP_MAP:
            op = 'u' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(self.block, op, lhs, rhs, name=name, flags=flags)
        self._insert(instr)
        return instr

    def select(self, cond, lhs, rhs, name=''):
        """
        Ternary select operator:
            name = cond ? lhs : rhs
        """
        instr = instructions.SelectInstr(self.block, cond, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    #
    # Cast APIs
    #

    @_castop('trunc')
    def trunc(self, value, typ, name=''):
        """
        Truncating integer downcast to a smaller type:
            name = (typ) value
        """

    @_castop('zext')
    def zext(self, value, typ, name=''):
        """
        Zero-extending integer upcast to a larger type:
            name = (typ) value
        """

    @_castop('sext')
    def sext(self, value, typ, name=''):
        """
        Sign-extending integer upcast to a larger type:
            name = (typ) value
        """

    @_castop('fptrunc')
    def fptrunc(self, value, typ, name=''):
        """
        Floating-point downcast to a less precise type:
            name = (typ) value
        """

    @_castop('fpext')
    def fpext(self, value, typ, name=''):
        """
        Floating-point upcast to a more precise type:
            name = (typ) value
        """

    @_castop('bitcast')
    def bitcast(self, value, typ, name=''):
        """
        Pointer cast to a different pointer type:
            name = (typ) value
        """

    @_castop('addrspacecast')
    def addrspacecast(self, value, typ, name=''):
        """
        Pointer cast to a different address space:
            name = (typ) value
        """

    @_castop('fptoui')
    def fptoui(self, value, typ, name=''):
        """
        Convert floating-point to unsigned integer:
            name = (typ) value
        """

    @_castop('uitofp')
    def uitofp(self, value, typ, name=''):
        """
        Convert unsigned integer to floating-point:
            name = (typ) value
        """

    @_castop('fptosi')
    def fptosi(self, value, typ, name=''):
        """
        Convert floating-point to signed integer:
            name = (typ) value
        """

    @_castop('sitofp')
    def sitofp(self, value, typ, name=''):
        """
        Convert signed integer to floating-point:
            name = (typ) value
        """

    @_castop('ptrtoint')
    def ptrtoint(self, value, typ, name=''):
        """
        Cast pointer to integer:
            name = (typ) value
        """

    @_castop('inttoptr')
    def inttoptr(self, value, typ, name=''):
        """
        Cast integer to pointer:
            name = (typ) value
        """

    #
    # Memory APIs
    #

    def alloca(self, typ, size=None, name=''):
        """
        Stack-allocate a slot for *size* elements of the given type.
        (default one element)
        """
        if size is None:
            pass
        elif isinstance(size, (values.Value, values.Constant)):
            assert isinstance(size.type, types.IntType)
        else:
            # If it is not a Value instance,
            # assume to be a Python integer.
            size = values.Constant(types.IntType(32), size)

        al = instructions.AllocaInstr(self.block, typ, size, name)
        self._insert(al)
        return al

    def load(self, ptr, name='', align=None):
        """
        Load value from pointer, with optional guaranteed alignment:
            name = *ptr
        """
        if not isinstance(ptr.type, types.PointerType):
            raise TypeError("cannot load from value of type %s (%r): not a pointer"
                            % (ptr.type, str(ptr)))
        ld = instructions.LoadInstr(self.block, ptr, name)
        ld.align = align
        self._insert(ld)
        return ld

    def store(self, value, ptr, align=None):
        """
        Store value to pointer, with optional guaranteed alignment:
            *ptr = name
        """
        if not isinstance(ptr.type, types.PointerType):
            raise TypeError("cannot store to value of type %s (%r): not a pointer"
                            % (ptr.type, str(ptr)))
        if ptr.type.pointee != value.type:
            raise TypeError("cannot store %s to %s: mismatching types"
                            % (value.type, ptr.type))
        st = instructions.StoreInstr(self.block, value, ptr)
        st.align = align
        self._insert(st)
        return st


    #
    # Terminators APIs
    #

    def switch(self, value, default):
        """
        Create a switch-case with a single *default* target.
        """
        swt = instructions.SwitchInstr(self.block, 'switch', value, default)
        self._set_terminator(swt)
        return swt

    def branch(self, target):
        """
        Unconditional branch to *target*.
        """
        br = instructions.Branch(self.block, "br", [target])
        self._set_terminator(br)
        return br

    def cbranch(self, cond, truebr, falsebr):
        """
        Conditional branch to *truebr* if *cond* is true, else to *falsebr*.
        """
        br = instructions.ConditionalBranch(self.block, "br",
                                            [cond, truebr, falsebr])
        self._set_terminator(br)
        return br

    def branch_indirect(self, addr):
        """
        Indirect branch to target *addr*.
        """
        br = instructions.IndirectBranch(self.block, "indirectbr", addr)
        self._set_terminator(br)
        return br

    def ret_void(self):
        """
        Return from function without a value.
        """
        return self._set_terminator(
            instructions.Ret(self.block, "ret void"))

    def ret(self, value):
        """
        Return from function with the given *value*.
        """
        return self._set_terminator(
            instructions.Ret(self.block, "ret", value))

    def resume(self, landingpad):
        """
        Resume an in-flight exception.
        """
        br = instructions.Branch(self.block, "resume", [landingpad])
        self._set_terminator(br)
        return br

    # Call APIs

    def call(self, fn, args, name='', cconv=None, tail=False):
        """
        Call function *fn* with *args*:
            name = fn(args...)
        """
        inst = instructions.CallInstr(self.block, fn, args, name=name,
                                      cconv=cconv, tail=tail)
        self._insert(inst)
        return inst

    def asm(self, ftype, asm, constraint, args, side_effect, name=''):
        """
        Inline assembler.
        """
        asm = instructions.InlineAsm(ftype, asm, constraint, side_effect)
        return self.call(asm, args, name)

    def load_reg(self, reg_type, reg_name, name=''):
        """
        Load a register value into an LLVM value.
          Example: v = load_reg(IntType(32), "eax")
        """
        ftype = types.FunctionType(reg_type, [])
        return self.asm(ftype, "", "={%s}" % reg_name, [], False, name)

    def store_reg(self, value, reg_type, reg_name, name=''):
        """
        Store an LLVM value inside a register
          Example: store_reg(Constant(IntType(32), 0xAAAAAAAA), IntType(32), "eax")
        """
        ftype = types.FunctionType(types.VoidType(), [reg_type])
        return self.asm(ftype, "", "{%s}" % reg_name, [value], True, name)

    def invoke(self, fn, args, normal_to, unwind_to, name='', cconv=None, tail=False):
        inst = instructions.InvokeInstr(self.block, fn, args, normal_to, unwind_to, name=name,
                                        cconv=cconv)
        self._set_terminator(inst)
        return inst

    # GEP APIs

    def gep(self, ptr, indices, inbounds=False, name=''):
        """
        Compute effective address (getelementptr):
            name = getelementptr ptr, <indices...>
        """
        instr = instructions.GEPInstr(self.block, ptr, indices,
                                      inbounds=inbounds, name=name)
        self._insert(instr)
        return instr

    # Aggregate APIs

    def extract_value(self, agg, idx, name=''):
        """
        Extract member number *idx* from aggregate.
        """
        if not isinstance(idx, (tuple, list)):
            idx = [idx]
        instr = instructions.ExtractValue(self.block, agg, idx, name=name)
        self._insert(instr)
        return instr

    def insert_value(self, agg, value, idx, name=''):
        """
        Insert *value* into member number *idx* from aggregate.
        """
        if not isinstance(idx, (tuple, list)):
            idx = [idx]
        instr = instructions.InsertValue(self.block, agg, value, idx, name=name)
        self._insert(instr)
        return instr

    # PHI APIs

    def phi(self, typ, name=''):
        inst = instructions.PhiInstr(self.block, typ, name=name)
        self._insert(inst)
        return inst

    # Special API

    def unreachable(self):
        inst = instructions.Unreachable(self.block)
        self._set_terminator(inst)
        return inst

    def atomic_rmw(self, op, ptr, val, ordering, name=''):
        inst = instructions.AtomicRMW(self.block, op, ptr, val, ordering, name=name)
        self._insert(inst)
        return inst

    def cmpxchg(self, ptr, cmp, val, ordering, failordering=None, name=''):
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
        inst = instructions.CmpXchg(self.block, ptr, cmp, val, ordering,
                                    failordering, name=name)
        self._insert(inst)
        return inst

    def landingpad(self, typ, name='', cleanup=False):
        inst = instructions.LandingPadInstr(self.block, typ, name, cleanup)
        self._insert(inst)
        return inst

    def assume(self, cond):
        """
        Optimizer hint: assume *cond* is always true.
        """
        fn = self.module.declare_intrinsic("llvm.assume")
        return self.call(fn, [cond])
