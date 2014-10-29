"""
Implementation of LLVM IR instructions.
"""

from __future__ import print_function, absolute_import

import struct

from . import types, _utils
from .values import Block, ConstOpMixin, Undefined, Value


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


class CallInstr(Instruction):
    def __init__(self, parent, func, args, name=''):
        super(CallInstr, self).__init__(parent, func.function_type.return_type,
                                        "call", [func] + list(args), name=name)
        self.args = args
        self.callee = func

    @property
    def called_function(self):
        """Alias for llvmpy"""
        return self.callee

    def descr(self, buf):
        args = ', '.join('{0} {1}'.format(a.type, a.get_reference())
                         for a in self.args)
        fnty = self.callee.type
        print("call {0} {1}({2})".format(fnty,
                                         self.callee.get_reference(),
                                         args),
              file=buf)


class Terminator(Instruction):
    def __new__(cls, parent, opname, *args):
        if opname == 'ret':
            cls = Ret
        elif opname == 'switch':
            cls = SwitchInstr
        else:
            cls = Terminator
        return object.__new__(cls)

    def __init__(self, parent, opname, operands):
        super(Terminator, self).__init__(parent, types.VoidType(), opname,
                                         operands)
        self.metadata = {}

    def descr(self, buf):
        opname = self.opname
        operands = ', '.join("{0} {1}".format(op.type, op.get_reference())
                             for op in self.operands)
        print("{opname} {operands} ".format(**locals()), file=buf, end='')


class Ret(Terminator):
    def descr(self, buf):
        msg = "ret {0} {1}".format(
            self.return_type, self.return_value.get_reference())
        print(msg, file=buf)

    @property
    def return_value(self):
        return self.operands[0]

    @property
    def return_type(self):
        return self.operands[0].type


def _as_float(value):
    """Truncate to single-precision float
    """
    return struct.unpack('f', struct.pack('f', value))[0]


def _format_float(value, packfmt, unpackfmt, numdigits):
    raw = struct.pack(packfmt, float(value))
    intrep = struct.unpack(unpackfmt, raw)[0]
    out = '{{0:#{0}x}}'.format(numdigits).format(intrep)
    return out


def _special_float_value(val):
    if val == val:
        return val == float('+inf') or val == float('-inf')
    return False


class Constant(ConstOpMixin):
    """
    Constant values
    """

    def __init__(self, typ, constant):
        assert not isinstance(typ, types.VoidType)
        self.type = typ
        self.constant = constant

    def __str__(self):
        return '{0} {1}'.format(self.type, self.get_reference())

    def get_reference(self):
        if isinstance(self.constant, bytearray):
            val = 'c"{0}"'.format(_escape_string(self.constant))

        elif self.constant is None:
            val = self.type.null

        elif self.constant is Undefined:
            val = "undef"

        elif isinstance(self.type, types.ArrayType):
            fmter = lambda x: "{0} {1}".format(x.type, x.get_reference())
            val = "[{0}]".format(', '.join(map(fmter, self.constant)))

        elif isinstance(self.type, types.StructType):
            fmter = lambda x: "{0} {1}".format(x.type, x.get_reference())
            val = "{{{0}}}".format(', '.join(map(fmter, self.constant)))

        elif isinstance(self.type, (types.FloatType, types.DoubleType)):
            if isinstance(self.type, types.FloatType):
                val = _as_float(self.constant)
            else:
                val = self.constant
            val = _format_float(val, 'd', 'Q', 16)

        else:
            val = str(self.constant)
        return val

    @classmethod
    def literal_struct(cls, elems):
        tys = [el.type for el in elems]
        return cls(types.LiteralStructType(tys), elems)


class ConstOp(object):
    def __init__(self, typ, op):
        self.type = typ
        self.op = op

    def __str__(self):
        return "{0}".format(self.op)

    def get_reference(self):
        return str(self)


class SelectInstr(Instruction):
    def __init__(self, parent, cond, lhs, rhs, name=''):
        assert lhs.type == rhs.type
        super(SelectInstr, self).__init__(parent, lhs.type, "select",
                                          [cond, lhs, rhs], name=name)
        self.cond = cond
        self.lhs = lhs
        self.rhs = rhs

    def descr(self, buf):
        print("select {0} {1}, {2} {3}, {4} {5}".format(
            self.cond.type, self.cond.get_reference(),
            self.lhs.type, self.lhs.get_reference(),
            self.rhs.type, self.rhs.get_reference()),
              file=buf)


class CompareInstr(Instruction):
    # Define the following in subclasses
    OPNAME = 'invalid-compare'
    VALID_OP = {}

    def __init__(self, parent, op, lhs, rhs, name=''):
        assert op in self.VALID_OP
        super(CompareInstr, self).__init__(parent, types.IntType(1),
                                           self.OPNAME, [lhs, rhs], name=name)
        self.op = op

    def descr(self, buf):
        print("{0} {1} {2} {3}, {4}".format(self.OPNAME, self.op,
                                            self.operands[0].type,
                                            self.operands[0].get_reference(),
                                            self.operands[1].get_reference()),
              file=buf)


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
        print("{0} {1} {2} to {3}".format(self.opname,
                                          self.operands[0].type,
                                          self.operands[0].get_reference(),
                                          self.type),
              file=buf)


class LoadInstr(Instruction):
    def __init__(self, parent, ptr, name=''):
        super(LoadInstr, self).__init__(parent, ptr.type.pointee, "load",
                                        [ptr], name=name)

    def descr(self, buf):
        [val] = self.operands
        print("load {0} {1}".format(val.type, val.get_reference()), file=buf)


class StoreInstr(Instruction):
    def __init__(self, parent, val, ptr):
        super(StoreInstr, self).__init__(parent, types.VoidType(), "store",
                                         [val, ptr])

    def descr(self, buf):
        val, ptr = self.operands
        print("store {0} {1}, {2} {3}".format(val.type, val.get_reference(),
                                              ptr.type, ptr.get_reference()),
              file=buf)


class AllocaInstr(Instruction):
    def __init__(self, parent, typ, count, name):
        operands = [count] if count else ()
        super(AllocaInstr, self).__init__(parent, typ.as_pointer(), "alloca",
                                          operands, name)

    def descr(self, buf):
        print("{0} {1}".format(self.opname, self.type.pointee),
              file=buf, end='')
        if self.operands:
            print(", {0} {1}".format(self.operands[0].type,
                                     self.operands[0].get_reference()),
                  file=buf)


class SwitchInstr(Terminator):
    def __init__(self, parent, opname, val, default):
        super(SwitchInstr, self).__init__(parent, opname, [val])
        self.value = val
        self.default = default
        self.cases = []

    def add_case(self, val, blk):
        assert isinstance(blk, Block)
        self.cases.append((val, blk))

    def descr(self, buf):
        cases = ["{0} {1}, label {2}".format(val.type, val.get_reference(),
                                             blk.get_reference())
                 for val, blk in self.cases]
        print("switch {0} {1}, label {2} [{3}]".format(self.value.type,
                                                       self.value.get_reference(),
                                                       self.default.get_reference(),
                                                       ' '.join(cases)),
              file=buf)


class GEPInstr(Instruction):
    def __init__(self, parent, ptr, indices, inbounds, name):
        typ = ptr.type
        for i in indices:
            typ = typ.gep(i)

        typ = typ.as_pointer()
        super(GEPInstr, self).__init__(parent, typ, "getelementptr",
                                       [ptr] + list(indices), name=name)
        self.pointer = ptr
        self.indices = indices
        self.inbounds = inbounds

    def descr(self, buf):
        indices = ['{0} {1}'.format(i.type, i.get_reference())
                   for i in self.indices]
        inbounds = "inbounds" if self.inbounds else ""
        print("getelementptr {0} {1} {2}, {3}".format(
            inbounds, self.pointer.type, self.pointer.get_reference(),
            ', '.join(indices)),
              file=buf)


class PhiInstr(Instruction):
    def __init__(self, parent, typ, name):
        super(PhiInstr, self).__init__(parent, typ, "phi", (), name=name)
        self.incomings = []

    def descr(self, buf):
        incs = ', '.join('[{0}, {1}]'.format(v.get_reference(),
                                             b.get_reference())
                         for v, b in self.incomings)
        print("phi {0} {1}".format(self.type, incs), file=buf)

    def add_incoming(self, value, block):
        assert isinstance(block, Block)
        self.incomings.append((value, block))


class ExtractValue(Instruction):
    def __init__(self, parent, agg, indices, name=''):
        typ = agg.type
        for i in indices:
            typ = typ.elements[i]

        super(ExtractValue, self).__init__(parent, typ, "extractvalue",
                                           [agg], name=name)

        self.aggregate = agg
        self.indices = indices

    def descr(self, buf):
        indices = [str(i) for i in self.indices]

        print("extractvalue {0} {1}, {2}".format(self.aggregate.type,
                                                 self.aggregate.get_reference(),
                                                 ', '.join(indices)),
              file=buf)


class InsertValue(Instruction):
    def __init__(self, parent, agg, elem, indices, name=''):
        typ = agg.type
        for i in indices:
            typ = typ.elements[i]
        assert elem.type == typ
        super(InsertValue, self).__init__(parent, agg.type, "insertvalue",
                                          [agg, elem], name=name)

        self.aggregate = agg
        self.value = elem
        self.indices = indices

    def descr(self, buf):
        indices = [str(i) for i in self.indices]

        print("insertvalue {0} {1}, {2} {3}, {4}".format(
            self.aggregate.type, self.aggregate.get_reference(),
            self.value.type, self.value.get_reference(),
            ', '.join(indices)),
              file=buf)


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
                         constraint=self.constraint),
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
        fmt = "atomicrmw {op} {ptrty} {ptr}, {ty} {val} {ordering}"
        print(fmt.format(op=self.operation,
                         ptrty=self.operands[0].type,
                         ptr=self.operands[0].get_reference(),
                         ty=self.operands[1].type,
                         val=self.operands[1].get_reference(),
                         ordering=self.ordering),
              file=buf)
