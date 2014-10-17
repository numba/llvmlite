"""
Classes that are LLVM values: Value, Constant, Instructions...
"""

from __future__ import print_function, absolute_import
from weakref import WeakSet
import string
import struct
from . import types, _utils

_VALID_CHARS = (frozenset(map(ord, string.ascii_letters)) |
                frozenset(map(ord, string.digits)))


def _escape_string(text):
    buf = []
    for ch in text:
        if ch in _VALID_CHARS:
            buf.append(chr(ch))
        else:
            ashex = hex(ch)[2:]
            if len(ashex) == 1:
                ashex = '0' + ashex
            buf.append('\\' + ashex)
    return ''.join(buf)


class Undefined(object):
    pass


def _wrapname(x):
    return '"{0}"'.format(x).replace(' ', '_')


class ConstOpMixin(object):
    def bitcast(self, typ):
        if typ == self.type:
            return self
        op = "bitcast ({0} {1} to {2})".format(self.type, self.get_reference(),
                                               typ)
        return ConstOp(typ, op)

    def inttoptr(self, typ):
        assert isinstance(self.type, types.IntType)
        assert isinstance(typ, types.PointerType)
        op = "inttoptr ({0} {1} to {2})".format(self.type,
                                                self.get_reference(),
                                                typ)
        return ConstOp(typ, op)


class Value(object):
    name_prefix = '%'
    deduplicate_name = True
    nested_scope = False

    def __init__(self, parent, type, name):
        assert parent is not None
        self.parent = parent
        self.type = type
        pscope = self.parent.scope
        self.scope = pscope.get_child() if self.nested_scope else pscope
        self._name = None
        self.name = name
        self.users = WeakSet()

    def __str__(self):
        with _utils.StringIO() as buf:
            if self.type == types.VoidType():
                self.descr(buf)
                return buf.getvalue().rstrip()
            else:
                name = self.get_reference()
                self.descr(buf)
                descr = buf.getvalue().rstrip()
                return "{name} = {descr}".format(**locals())

    def descr(self, buf):
        raise NotImplementedError

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if self.deduplicate_name:
            name = self.scope.deduplicate(name)

        self.scope.register(name)
        self._name = name

    def get_reference(self):
        return self.name_prefix + _wrapname(self.name)


class MetaDataString(Value):
    def __init__(self, parent, string):
        super(MetaDataString, self).__init__(parent, types.MetaData, name="")
        self.string = string

    def descr(self, buf):
        print("!\"{0}\"".format(self.string), file=buf)

    def get_reference(self):
        return "metadata !\"{0}\"".format(self.string)

    def __str__(self):
        return self.get_reference()


class MetaData(Value):
    name_prefix = '!'

    def __init__(self, parent, values, name):
        super(MetaData, self).__init__(parent, types.MetaData, name=name)
        self.operands = tuple(values)
        parent.metadata.append(self)

    @property
    def operand_count(self):
        return len(self.operands)

    def descr(self, buf):
        operands = ', '.join(str(op) for op in self.operands)
        print("metadata !{{ {operands} }}".format(operands=operands), file=buf)


class GlobalValue(Value, ConstOpMixin):
    name_prefix = '@'
    deduplicate_name = False

    def __init__(self, *args, **kwargs):
        super(GlobalValue, self).__init__(*args, **kwargs)
        self.linkage = ''


class GlobalVariable(GlobalValue):
    def __init__(self, module, typ, name):
        super(GlobalVariable, self).__init__(module, typ.as_pointer(),
                                             name=name)
        self.gtype = typ
        self.initializer = None
        self.global_constant = False
        self.parent.add_global(self)

    def descr(self, buf):
        if self.global_constant:
            kind = 'constant'
        else:
            kind = 'global'

        if not self.global_constant:
            linkage = 'external'
        else:
            linkage = ''

        print("{0} {1} {2} ".format(linkage, kind, self.gtype), file=buf,
              end='')

        if self.initializer is not None:
            print(self.initializer.get_reference(), file=buf, end='')
            # else:
        #     print('undef', file=buf, end='')

        print(file=buf)


class AttributeSet(set):
    _known = ()

    def add(self, name):
        assert name in self._known
        return super(AttributeSet, self).add(name)


class FunctionAttributes(AttributeSet):
    _known = frozenset(['alwaysinline', 'builtin', 'cold', 'inlinehint',
                        'jumptable', 'minsize', 'naked', 'nobuiltin',
                        'noduplicate', 'noimplicitfloat', 'noinline',
                        'nonlazybind', 'noredzone', 'noreturn', 'nounwind',
                        'optnone', 'optsize', 'readnone', 'readonly',
                        'returns_twice', 'sanitize_address',
                        'sanitize_memory', 'sanitize_thread', 'ssp',
                        'sspreg', 'sspstrong', 'uwtable'])

    def __init__(self):
        self._alignstack = 0

    @property
    def alignstack(self):
        return self._alignstack

    @alignstack.setter
    def alignstack(self, val):
        assert val >= 0
        self._alignstack = val

    def __repr__(self):
        attrs = list(self)
        if self.alignstack:
            attrs.append('alignstack({:u})'.format(self.alignstack))
        return ', '.join(attrs)


class Function(GlobalValue):
    """Represent a LLVM Function but does uses a Module as parent.
    Global Values are stored as a set of dependencies (attribute `depends`).
    """
    nested_scope = True

    def __init__(self, module, ftype, name):
        super(Function, self).__init__(module, ftype.as_pointer(), name=name)
        self.ftype = ftype
        self.blocks = []
        self.attributes = FunctionAttributes()
        self.args = tuple([Argument(self, i, t)
                           for i, t in enumerate(ftype.args)])
        self.parent.add_global(self)

    @property
    def module(self):
        return self.parent

    @property
    def entry_basic_block(self):
        return self.blocks[0]

    @property
    def basic_blocks(self):
        return self.blocks

    def append_basic_block(self, name=''):
        blk = Block(parent=self, name=name)
        self.blocks.append(blk)
        return blk

    def insert_basic_block(self, before, name=''):
        """Insert block before
        """
        blk = Block(parent=self, name=name)
        self.blocks.insert(before, blk)
        return blk

    def descr_prototype(self, buf):
        """
        Describe the prototype ("head") of the function.
        """
        state = "define" if self.blocks else "declare"
        retty = self.ftype.return_type
        args = ", ".join(str(a) for a in self.args)
        name = self.get_reference()
        attrs = self.attributes
        vararg = ', ...' if self.ftype.var_arg else ''
        linkage = self.linkage
        prototype = "{state} {linkage} {retty} {name}({args}{vararg}) {attrs}" \
            .format(
            **locals())
        print(prototype, file=buf)

    def descr_body(self, buf):
        """
        Describe of the body of the function.
        """
        for blk in self.blocks:
            blk.descr(buf)

    def descr(self, buf):
        self.descr_prototype(buf)
        if self.blocks:
            print('{', file=buf)
            self.descr_body(buf)
            print('}', file=buf)

    def __str__(self):
        with _utils.StringIO() as buf:
            self.descr(buf)
            return buf.getvalue()

    @property
    def is_declaration(self):
        return len(self.blocks) == 0


class ArgumentAttributes(AttributeSet):
    _known = frozenset(['nocapture'])  # TODO


class Argument(Value):
    def __init__(self, parent, pos, typ, name=''):
        super(Argument, self).__init__(parent, typ, name=name)
        self.parent = parent
        self.pos = pos
        self.attributes = ArgumentAttributes()

    def __str__(self):
        return "{0} {1} {2}".format(self.type, ' '.join(self.attributes),
                                    self.get_reference())

    def add_attribute(self, attr):
        self.attributes.add(attr)


class Block(Value):
    def __init__(self, parent, name=''):
        super(Block, self).__init__(parent, types.LabelType(), name=name)
        self.instructions = []
        self.terminator = None

    @property
    def is_terminated(self):
        return self.terminator is not None

    @property
    def function(self):
        return self.parent

    def descr(self, buf):
        print("{0}:".format(self.name), file=buf)
        for instr in self.instructions:
            print('  ', end='', file=buf)
            print(instr, file=buf)


class Instruction(Value):
    def __init__(self, parent, typ, opname, operands, name=''):
        super(Instruction, self).__init__(parent, typ, name=name)
        assert isinstance(parent, Block)
        self.opname = opname
        self.operands = operands

        for op in self.operands:
            op.users.add(self)

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
        super(CallInstr, self).__init__(parent, func.type.pointee.return_type,
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
        fnty = self.callee.type.pointee
        print("call {0} {1}({2})".format(fnty.as_pointer(),
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
        self.users = WeakSet()

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
        self.users = WeakSet()

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

