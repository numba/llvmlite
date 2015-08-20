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
            assert lhs.type == rhs.type, "Operands must be the same type"
            instr = cls(self.block, lhs.type, opname, (lhs, rhs), name, flags)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


def _binop_with_overflow(opname, cls=instructions.Instruction):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, lhs, rhs, name=''):
            assert lhs.type == rhs.type, "Operands must be the same type"
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

    @property
    def block(self):
        return self._block

    basic_block = block

    @property
    def function(self):
        return self.block.parent

    @property
    def module(self):
        return self.block.parent.module

    def position_before(self, instr):
        self._block = instr.parent
        self._anchor = self._block.instructions.index(instr)

    def position_after(self, instr):
        self._block = instr.parent
        self._anchor = self._block.instructions.index(instr) + 1

    def position_at_start(self, block):
        self._block = block
        self._anchor = 0

    def position_at_end(self, block):
        self._block = block
        self._anchor = len(block.instructions)

    def append_basic_block(self, name=''):
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
        pass

    @_binop('lshr')
    def lshr(self, lhs, rhs, name=''):
        pass

    @_binop('ashr')
    def ashr(self, lhs, rhs, name=''):
        pass

    @_binop('add')
    def add(self, lhs, rhs, name=''):
        pass

    @_binop('fadd')
    def fadd(self, lhs, rhs, name=''):
        pass

    @_binop('sub')
    def sub(self, lhs, rhs, name=''):
        pass

    @_binop('fsub')
    def fsub(self, lhs, rhs, name=''):
        pass

    @_binop('mul')
    def mul(self, lhs, rhs, name=''):
        pass

    @_binop('fmul')
    def fmul(self, lhs, rhs, name=''):
        pass

    @_binop('udiv')
    def udiv(self, lhs, rhs, name=''):
        pass

    @_binop('sdiv')
    def sdiv(self, lhs, rhs, name=''):
        pass

    @_binop('fdiv')
    def fdiv(self, lhs, rhs, name=''):
        pass

    @_binop('urem')
    def urem(self, lhs, rhs, name=''):
        pass

    @_binop('srem')
    def srem(self, lhs, rhs, name=''):
        pass

    @_binop('frem')
    def frem(self, lhs, rhs, name=''):
        pass

    @_binop('or')
    def or_(self, lhs, rhs, name=''):
        pass

    @_binop('and')
    def and_(self, lhs, rhs, name=''):
        pass

    @_binop('xor')
    def xor(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('sadd')
    def sadd_with_overflow(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('smul')
    def smul_with_overflow(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('ssub')
    def ssub_with_overflow(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('uadd')
    def uadd_with_overflow(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('umul')
    def umul_with_overflow(self, lhs, rhs, name=''):
        pass

    @_binop_with_overflow('usub')
    def usub_with_overflow(self, lhs, rhs, name=''):
        pass

    #
    # Unary APIs
    #

    def not_(self, value, name=''):
        return self.xor(value, values.Constant(value.type, -1), name=name)

    def neg(self, value, name=''):
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
        return self._icmp('s', cmpop, lhs, rhs, name)

    def icmp_unsigned(self, cmpop, lhs, rhs, name=''):
        return self._icmp('u', cmpop, lhs, rhs, name)

    def fcmp_ordered(self, cmpop, lhs, rhs, name=''):
        if cmpop in _CMP_MAP:
            op = 'o' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(self.block, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def fcmp_unordered(self, cmpop, lhs, rhs, name=''):
        if cmpop in _CMP_MAP:
            op = 'u' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = instructions.FCMPInstr(self.block, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def select(self, cond, lhs, rhs, name=''):
        instr = instructions.SelectInstr(self.block, cond, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    #
    # Cast APIs
    #

    @_castop('trunc')
    def trunc(self, value, typ, name=''):
        pass

    @_castop('zext')
    def zext(self, value, typ, name=''):
        pass

    @_castop('sext')
    def sext(self, value, typ, name=''):
        pass

    @_castop('fptrunc')
    def fptrunc(self, value, typ, name=''):
        pass

    @_castop('fpext')
    def fpext(self, value, typ, name=''):
        pass

    @_castop('bitcast')
    def bitcast(self, value, typ, name=''):
        pass

    @_castop('fptoui')
    def fptoui(self, value, typ, name=''):
        pass

    @_castop('uitofp')
    def uitofp(self, value, typ, name=''):
        pass

    @_castop('fptosi')
    def fptosi(self, value, typ, name=''):
        pass

    @_castop('sitofp')
    def sitofp(self, value, typ, name=''):
        pass

    @_castop('ptrtoint')
    def ptrtoint(self, value, typ, name=''):
        pass

    @_castop('inttoptr')
    def inttoptr(self, value, typ, name=''):
        pass

    @_castop('addrspacecast')
    def addrspacecast(self, value, typ, name=''):
        pass

    #
    # Memory APIs
    #

    def alloca(self, typ, size=None, name=''):
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

    def load(self, ptr, name=''):
        if not isinstance(ptr.type, types.PointerType):
            raise TypeError("cannot load from value of type %s (%r): not a pointer"
                            % (ptr.type, str(ptr)))
        ld = instructions.LoadInstr(self.block, ptr, name)
        self._insert(ld)
        return ld

    def store(self, value, ptr):
        if not isinstance(ptr.type, types.PointerType):
            raise TypeError("cannot store to value of type %s (%r): not a pointer"
                            % (ptr.type, str(ptr)))
        st = instructions.StoreInstr(self.block, value, ptr)
        self._insert(st)
        return st


    #
    # Terminators APIs
    #

    def switch(self, value, default):
        swt = instructions.SwitchInstr(self.block, 'switch', value, default)
        self._set_terminator(swt)
        return swt

    def branch(self, target):
        """Jump to target
        """
        br = instructions.Branch(self.block, "br", [target])
        self._set_terminator(br)
        return br

    def cbranch(self, cond, truebr, falsebr):
        """Branch conditionally
        """
        br = instructions.ConditionalBranch(self.block, "br",
                                            [cond, truebr, falsebr])
        self._set_terminator(br)
        return br

    def branch_indirect(self, addr):
        """Branch indirectly
        """
        br = instructions.IndirectBranch(self.block, "indirectbr", addr)
        self._set_terminator(br)
        return br

    def ret_void(self):
        return self._set_terminator(
            instructions.Ret(self.block, "ret void"))

    def ret(self, value):
        return self._set_terminator(
            instructions.Ret(self.block, "ret", value))

    def resume(self, landingpad):
        """Resume an in-flight exception
        """
        br = instructions.Branch(self.block, "resume", [landingpad])
        self._set_terminator(br)
        return br

    # Call APIs

    def call(self, fn, args, name='', cconv=None, tail=False):
        inst = instructions.CallInstr(self.block, fn, args, name=name,
                                      cconv=cconv, tail=tail)
        self._insert(inst)
        return inst

    def invoke(self, fn, args, normal_to, unwind_to, name='', cconv=None, tail=False):
        inst = instructions.InvokeInstr(self.block, fn, args, normal_to, unwind_to, name=name,
                                        cconv=cconv)
        self._set_terminator(inst)
        return inst

    # GEP APIs

    def gep(self, ptr, indices, inbounds=False, name=''):
        instr = instructions.GEPInstr(self.block, ptr, indices,
                                      inbounds=inbounds, name=name)
        self._insert(instr)
        return instr

    # Aggregate APIs

    def extract_value(self, agg, idx, name=''):
        if not isinstance(idx, (tuple, list)):
            idx = [idx]
        instr = instructions.ExtractValue(self.block, agg, idx, name=name)
        self._insert(instr)
        return instr

    def insert_value(self, agg, value, idx, name=''):
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
        If failordering is `None`, the value of `ordering` is used.
        """
        failordering = ordering if failordering is None else failordering
        inst = instructions.CmpXchg(self.block, ptr, cmp, val, ordering,
                                    failordering, name=name)
        self._insert(inst)
        return inst

    def landingpad(self, typ, personality, name='', cleanup=False):
        inst = instructions.LandingPadInstr(self.block, typ, personality, name, cleanup)
        self._insert(inst)
        return inst

    def assume(self, cond):
        fn = self.module.declare_intrinsic("llvm.assume")
        return self.call(fn, [cond])

