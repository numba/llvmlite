"""
Implementation of LLVM IR instructions.
"""

from __future__ import print_function, absolute_import

from . import types, _utils
from .values import Block, Function, Value


class Instruction(Value):
    def __init__(self, parent, typ, opname, operands, name=''):
        super(Instruction, self).__init__(parent, typ, name=name)
        assert isinstance(parent, Block)
        self.opname = opname
        self.operands = operands

        self.metadata = {}

    def _stringify_metatdata(self):
        buf = []

        if self.metadata:
            for k, v in self.metadata.items():
                buf.append("!{0} {1}".format(k, v.get_reference()))
            return ', ' + ', '.join(buf)
        else:
            return ''

    def set_metadata(self, name, node):
        self.metadata[name] = node

    def descr(self, buf):
        opname = self.opname
        operands = ', '.join(op.get_reference() for op in self.operands)
        typ = self.type
        metadata = self._stringify_metatdata()
        print("{opname} {typ} {operands}{metadata}".format(**locals()),
              file=buf)

    def replace_usage(self, old, new):
        if old in self.operands:
            ops = []
            for op in self.operands:
                ops.append(new if op is old else op)
            self.operands = tuple(ops)


class CallInstr(Instruction):
    def __init__(self, parent, func, args, name='', cconv=None, tail=False):
        self.cconv = (func.calling_convention
                      if cconv is None and isinstance(func, Function)
                      else cconv)
        self.tail = tail
        super(CallInstr, self).__init__(parent, func.function_type.return_type,
                                        "call", [func] + list(args), name=name)
        # Validate
        for argno, (arg, exptype) in enumerate(zip(self.args,
                                               self.callee.function_type.args)):
            if arg.type != exptype:
                msg = "Type of #{0} arg mismatch: {1} != {2}"
                raise TypeError(msg.format(1 + argno, exptype, arg.type))

    @property
    def callee(self):
        return self.operands[0]

    @callee.setter
    def callee(self, newcallee):
        self.operands[0] = newcallee

    @property
    def args(self):
        return self.operands[1:]

    def replace_callee(self, newfunc):
        if newfunc.function_type != self.callee.function_type:
            raise TypeError("New function has incompatible type")
        self.callee = newfunc

    @property
    def called_function(self):
        """Alias for llvmpy"""
        return self.callee

    def descr(self, buf):
        args = ', '.join('{0} {1}'.format(a.type, a.get_reference())
                         for a in self.args)
        fnty = self.callee.type
        callee_ref = "{0} {1}".format(fnty, self.callee.get_reference())
        if self.cconv:
            callee_ref = "{0} {1}".format(self.cconv, callee_ref)
        print("{tail}call {callee}({args}){metadata}".format(
            tail='tail ' if self.tail else '',
            callee=callee_ref,
            args=args,
            metadata=self._stringify_metatdata(),
            ), file=buf)


class Terminator(Instruction):
    def __init__(self, parent, opname, operands):
        super(Terminator, self).__init__(parent, types.VoidType(), opname,
                                         operands)
        self.metadata = {}

    def descr(self, buf):
        opname = self.opname
        operands = ', '.join("{0} {1}".format(op.type, op.get_reference())
                             for op in self.operands)
        metadata = self._stringify_metatdata()
        print("{opname} {operands} {metadata}".format(**locals()), file=buf,
              end='')


class Ret(Terminator):
    def __init__(self, parent, opname, return_value=None):
        operands = [return_value] if return_value is not None else []
        super(Ret, self).__init__(parent, opname, operands)

    @property
    def return_value(self):
        if self.operands:
            return self.operands[0]
        else:
            return None

    def descr(self, buf):
        return_value = self.return_value
        if return_value is not None:
            msg = "{0} {1} {2}".format(self.opname, return_value.type,
                                       return_value.get_reference())
        else:
            msg = str(self.opname)
        print(msg, file=buf)


class SwitchInstr(Terminator):
    def __init__(self, parent, opname, val, default):
        super(SwitchInstr, self).__init__(parent, opname, [val])
        self.default = default
        self.cases = []

    @property
    def value(self):
        return self.operands[0]

    def add_case(self, val, blk):
        assert isinstance(blk, Block)
        self.cases.append((val, blk))

    def descr(self, buf):
        cases = ["{0} {1}, label {2}".format(val.type, val.get_reference(),
                                             blk.get_reference())
                 for val, blk in self.cases]
        print("switch {0} {1}, label {2} [{3}]  {metadata}".format(
            self.value.type,
            self.value.get_reference(),
            self.default.get_reference(),
            ' '.join(cases),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class SelectInstr(Instruction):
    def __init__(self, parent, cond, lhs, rhs, name=''):
        assert lhs.type == rhs.type
        super(SelectInstr, self).__init__(parent, lhs.type, "select",
                                          [cond, lhs, rhs], name=name)

    @property
    def cond(self):
        return self.operands[0]

    @property
    def lhs(self):
        return self.operands[1]

    @property
    def rhs(self):
        return self.operands[2]

    def descr(self, buf):
        print("select {0} {1}, {2} {3}, {4} {5} {metadata}".format(
            self.cond.type, self.cond.get_reference(),
            self.lhs.type, self.lhs.get_reference(),
            self.rhs.type, self.rhs.get_reference(),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class CompareInstr(Instruction):
    # Define the following in subclasses
    OPNAME = 'invalid-compare'
    VALID_OP = {}

    def __init__(self, parent, op, lhs, rhs, name=''):
        if op not in self.VALID_OP:
            raise ValueError("invalid comparison %r for %s" % (op, self.OPNAME))
        super(CompareInstr, self).__init__(parent, types.IntType(1),
                                           self.OPNAME, [lhs, rhs], name=name)
        self.op = op

    def descr(self, buf):
        print("{0} {1} {2} {3}, {4}{metadata}".format(
            self.OPNAME,
            self.op,
            self.operands[0].type,
            self.operands[0].get_reference(),
            self.operands[1].get_reference(),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class ICMPInstr(CompareInstr):
    OPNAME = 'icmp'
    VALID_OP = {
        'eq': 'equal',
        'ne': 'not equal',
        'ugt': 'unsigned greater than',
        'uge': 'unsigned greater or equal',
        'ult': 'unsigned less than',
        'ule': 'unsigned less or equal',
        'sgt': 'signed greater than',
        'sge': 'signed greater or equal',
        'slt': 'signed less than',
        'sle': 'signed less or equal',
    }


class FCMPInstr(CompareInstr):
    OPNAME = 'fcmp'
    VALID_OP = {
        'false': 'no comparison, always returns false',
        'oeq': 'ordered and equal',
        'ogt': 'ordered and greater than',
        'oge': 'ordered and greater than or equal',
        'olt': 'ordered and less than',
        'ole': 'ordered and less than or equal',
        'one': 'ordered and not equal',
        'ord': 'ordered (no nans)',
        'ueq': 'unordered or equal',
        'ugt': 'unordered or greater than',
        'uge': 'unordered or greater than or equal',
        'ult': 'unordered or less than',
        'ule': 'unordered or less than or equal',
        'une': 'unordered or not equal',
        'uno': 'unordered (either nans)',
        'true': 'no comparison, always returns true',
    }


class CastInstr(Instruction):
    def __init__(self, parent, op, val, typ, name=''):
        super(CastInstr, self).__init__(parent, typ, op, [val], name=name)

    def descr(self, buf):
        print("{0} {1} {2} to {3}{metadata}".format(
            self.opname,
            self.operands[0].type,
            self.operands[0].get_reference(),
            self.type,
            metadata=self._stringify_metatdata(),
            ), file=buf)


class LoadInstr(Instruction):
    def __init__(self, parent, ptr, name=''):
        super(LoadInstr, self).__init__(parent, ptr.type.pointee, "load",
                                        [ptr], name=name)

    def descr(self, buf):
        [val] = self.operands
        print("load {0} {1}{metadata}".format(
            val.type, val.get_reference(),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class StoreInstr(Instruction):
    def __init__(self, parent, val, ptr):
        super(StoreInstr, self).__init__(parent, types.VoidType(), "store",
                                         [val, ptr])

    def descr(self, buf):
        val, ptr = self.operands
        print("store {0} {1}, {2} {3}{metadata}".format(
            val.type, val.get_reference(),
            ptr.type, ptr.get_reference(),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class AllocaInstr(Instruction):
    def __init__(self, parent, typ, count, name):
        operands = [count] if count else ()
        super(AllocaInstr, self).__init__(parent, typ.as_pointer(), "alloca",
                                          operands, name)

    def descr(self, buf):
        print("{0} {1}".format(self.opname, self.type.pointee),
              file=buf, end='')
        if self.operands:
            print(", {0} {1}".format(
                self.operands[0].type,
                self.operands[0].get_reference(),
                ), file=buf, end='')
        if self.metadata:
            print(self._stringify_metatdata(), file=buf)


class GEPInstr(Instruction):
    def __init__(self, parent, ptr, indices, inbounds, name):
        typ = ptr.type
        lasttyp = None
        for i in indices:
            lasttyp, typ = typ, typ.gep(i)

        if (not isinstance(typ, types.PointerType) and
                isinstance(lasttyp, types.PointerType)):
            typ = lasttyp
        else:
            typ = typ.as_pointer()

        super(GEPInstr, self).__init__(parent, typ, "getelementptr",
                                       [ptr] + list(indices), name=name)
        self.pointer = ptr
        self.indices = indices
        self.inbounds = inbounds

    def descr(self, buf):
        indices = ['{0} {1}'.format(i.type, i.get_reference())
                   for i in self.indices]
        head = "getelementptr inbounds" if self.inbounds else "getelementptr"
        print("{0} {1} {2}, {3} {metadata}".format(
                  head,
                  self.pointer.type,
                  self.pointer.get_reference(),
                  ', '.join(indices),
                  metadata=self._stringify_metatdata(),
                  ), file=buf)


class PhiInstr(Instruction):
    def __init__(self, parent, typ, name):
        super(PhiInstr, self).__init__(parent, typ, "phi", (), name=name)
        self.incomings = []

    def descr(self, buf):
        incs = ', '.join('[{0}, {1}]'.format(v.get_reference(),
                                             b.get_reference())
                         for v, b in self.incomings)
        print("phi {0} {1} {metadata}".format(
            self.type, incs, metadata=self._stringify_metatdata(),
            ), file=buf)

    def add_incoming(self, value, block):
        assert isinstance(block, Block)
        self.incomings.append((value, block))

    def replace_usage(self, old, new):
        self.incomings = [((new if val is old else val), blk)
                          for (val, blk) in self.incomings]


class ExtractValue(Instruction):
    def __init__(self, parent, agg, indices, name=''):
        typ = agg.type
        try:
            for i in indices:
                typ = typ.elements[i]
        except (AttributeError, IndexError):
            raise TypeError("Can't index at %r in %s"
                            % (list(indices), agg.type))

        super(ExtractValue, self).__init__(parent, typ, "extractvalue",
                                           [agg], name=name)

        self.aggregate = agg
        self.indices = indices

    def descr(self, buf):
        indices = [str(i) for i in self.indices]

        print("extractvalue {0} {1}, {2} {metadata}".format(
            self.aggregate.type,
            self.aggregate.get_reference(),
            ', '.join(indices),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class InsertValue(Instruction):
    def __init__(self, parent, agg, elem, indices, name=''):
        typ = agg.type
        try:
            for i in indices:
                typ = typ.elements[i]
        except (AttributeError, IndexError):
            raise TypeError("Can't index at %r in %s"
                            % (list(indices), agg.type))
        if elem.type != typ:
            raise TypeError("Can only insert %s at %r in %s: got %s"
                            % (typ, list(indices), agg.type, elem.type))
        super(InsertValue, self).__init__(parent, agg.type, "insertvalue",
                                          [agg, elem], name=name)

        self.aggregate = agg
        self.value = elem
        self.indices = indices

    def descr(self, buf):
        indices = [str(i) for i in self.indices]

        print("insertvalue {0} {1}, {2} {3}, {4} {metadata}".format(
            self.aggregate.type, self.aggregate.get_reference(),
            self.value.type, self.value.get_reference(),
            ', '.join(indices),
            metadata=self._stringify_metatdata(),
            ), file=buf)


class Unreachable(Instruction):
    def __init__(self, parent):
        super(Unreachable, self).__init__(parent, types.VoidType(),
                                          "unreachable", (), name='')

    def descr(self, buf):
        print(self.opname, file=buf)


class InlineAsm(object):
    def __init__(self, ftype, asm, constraint, side_effect=False):
        self.type = ftype.return_type
        self.function_type = ftype
        self.asm = asm
        self.constraint = constraint
        self.side_effect = side_effect

    def descr(self, buf):
        sideeffect = 'sideeffect' if self.side_effect else ''
        fmt = "asm {sideeffect} \"{asm}\", \"{constraint}\""
        print(fmt.format(sideeffect=sideeffect, asm=self.asm,
                         constraint=self.constraint,),
              file=buf, end='')

    def get_reference(self):
        with _utils.StringIO() as buf:
            self.descr(buf)
            return buf.getvalue()

    def __str__(self):
        return "{0} {1}".format(self.type, self.get_reference())


class AtomicRMW(Instruction):
    def __init__(self, parent, op, ptr, val, ordering, name):
        super(AtomicRMW, self).__init__(parent, val.type, "atomicrmw",
                                        (ptr, val), name=name)
        self.operation = op
        self.ordering = ordering

    def descr(self, buf):
        fmt = "atomicrmw {op} {ptrty} {ptr}, {ty} {val} {ordering} {metadata}"
        print(fmt.format(op=self.operation,
                         ptrty=self.operands[0].type,
                         ptr=self.operands[0].get_reference(),
                         ty=self.operands[1].type,
                         val=self.operands[1].get_reference(),
                         ordering=self.ordering,
                         metadata=self._stringify_metatdata(),),
              file=buf)


class CmpXchg(Instruction):
    """This instruction has changed since llvm3.5.  It is not compatible with
    older llvm versions.
    """
    def __init__(self, parent, ptr, cmp, val, ordering, failordering, name):
        outtype = types.LiteralStructType([val.type, types.IntType(1)])
        super(CmpXchg, self).__init__(parent, outtype, "cmpxchg",
                                      (ptr, cmp, val), name=name)
        self.ordering = ordering
        self.failordering = failordering

    def descr(self, buf):
        fmt = "cmpxchg {ptrty} {ptr}, {ty} {cmp}, {ty} {val} {ordering} " \
              "{failordering} {metadata}"
        print(fmt.format(ptrty=self.operands[0].type,
                         ptr=self.operands[0].get_reference(),
                         ty=self.operands[1].type,
                         cmp=self.operands[1].get_reference(),
                         val=self.operands[2].get_reference(),
                         ordering=self.ordering,
                         failordering=self.failordering,
                         metadata=self._stringify_metatdata(), ),
              file=buf)
