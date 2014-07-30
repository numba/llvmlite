from __future__ import print_function, absolute_import
from weakref import WeakSet
import io

from . import lltypes
from purellvmpy.core import _utils


class Value(object):
    name_prefix = '%'
    nested_scope = False
    deduplicate_name = True

    def __init__(self, parent, type, name):
        assert parent is not None
        self.parent = parent
        self.type = type
        self.name_manager = (_utils.NameManager()
                             if self.nested_scope
                             else self.parent.name_manager)
        self._name = None
        self.name = name
        self.users = WeakSet()

    def __str__(self):
        with io.StringIO() as buf:
            if self.type == lltypes.VoidType():
                self.descr(buf)
                return buf.getvalue().rstrip()
            else:
                name = self.get_reference()
                self.descr(buf)
                descr = buf.getvalue().rstrip()
                return "%(name)s = %(descr)s" % locals()

    def descr(self, buf):
        raise NotImplementedError

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if self.deduplicate_name:
            name = self.name_manager.deduplicate(name)
        if name in self.name_manager:
            print(self.name_manager.used)
            raise NameError("Duplicated name '%s'" % name)
        self._name = name

    def get_reference(self):
        return self.name_prefix + self.name


class GlobalValue(Value):
    name_prefix = '@'
    deduplicate_name = False


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
            attrs.append('alignstack(%u)' % self.alignstack)
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
        self.args = [Argument(self, i, t) for i, t in enumerate(ftype.args)]
        self.parent.add_global(self)

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
        prototype = "%(state)s %(retty)s %(name)s(%(args)s) %(attrs)s" % \
                    locals()
        print(prototype, file=buf)

    def descr_body(self, buf):
        """
        Describe of the body of the function.
        """
        for blk in self.blocks:
            print("%s:" % blk.name, file=buf)
            for instr in blk.instructions:
                print('  ', end='', file=buf)
                print(instr, file=buf)

            if blk.is_terminated:
                print('  ', end='', file=buf)
                print(blk.terminator, file=buf)

    def descr(self, buf):
        self.descr_prototype(buf)
        if self.blocks:
            print('{', file=buf)
            self.descr_body(buf)
            print('}', file=buf)

    def __str__(self):
        with io.StringIO() as buf:
            self.descr(buf)
            return buf.getvalue()


class ArgumentAttributes(AttributeSet):
    _known = frozenset([])  # TODO


class Argument(Value):
    def __init__(self, parent, pos, typ, name=''):
        super(Argument, self).__init__(parent, typ, name=name)
        self.parent = parent
        self.pos = pos
        self.attributes = ArgumentAttributes()

    def __str__(self):
        return "%s %s" % (self.type, self.get_reference())


class Block(Value):
    def __init__(self, parent, name=''):
        super(Block, self).__init__(parent, lltypes.LabelType(), name=name)
        self.instructions = []
        self.terminator = None

    @property
    def is_terminated(self):
        return self.terminator is not None


class Instruction(Value):
    def __init__(self, parent, typ, opname, operands, name=''):
        super(Instruction, self).__init__(parent, typ, name=name)
        self.opname = opname
        self.operands = operands

        for op in self.operands:
            op.users.add(self)

    def descr(self, buf):
        opname = self.opname
        operands = ', '.join(op.get_reference() for op in self.operands)
        typ = self.type
        print("%(opname)s %(typ)s %(operands)s" % locals(), file=buf)


class Terminator(Instruction):
    def __new__(cls, parent, opname, operands, name=''):
        if opname == 'ret':
            cls = Ret
        else:
            cls = Terminator
        return object.__new__(cls)

    def __init__(self, parent, opname, operands, name=''):
        super(Terminator, self).__init__(parent, lltypes.VoidType(), opname,
                                         operands,
                                         name=name)

    def descr(self, buf):
        opname = self.opname
        operands = ', '.join("%s %s" % (op.type, op.get_reference())
                             for op in self.operands)
        print("%(opname)s %(operands)s" % locals(), file=buf)


class Ret(Terminator):
    def descr(self, buf):
        msg = "ret %s %s" % (
            self.return_type, self.return_value.get_reference())
        print(msg, file=buf)

    @property
    def return_value(self):
        return self.operands[0]

    @property
    def return_type(self):
        return self.operands[0].type


class Constant(object):
    """
    Constant values
    """

    def __init__(self, typ, constant):
        assert not isinstance(typ, lltypes.VoidType)
        self.type = typ
        self.constant = constant
        self.users = WeakSet()

    def __str__(self):
        return "%s %s" % (self.type, self.constant)

    def get_reference(self):
        return str(self.constant)


class CompareInstr(Instruction):
    # Define the following in subclasses
    OPNAME = 'invalid-compare'
    VALID_OP = {}

    def __init__(self, parent, op, lhs, rhs, name=''):
        assert op in self.VALID_OP
        super(CompareInstr, self).__init__(parent, lltypes.IntType(1),
                                           self.OPNAME, [lhs, rhs], name=name)
        self.op = op

    def descr(self, buf):
        print("icmp %s %s %s, %s" % (self.op,
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
        print("%s %s %s to %s" % (self.opname, self.operands[0].type,
                                  self.operands[0].get_reference(),
                                  self.type),
              file=buf)


class LoadInstr(Instruction):
    def __init__(self, parent, ptr, name=''):
        super(LoadInstr, self).__init__(parent, ptr.type.pointee, "load",
                                        [ptr], name=name)

    def descr(self, buf):
        [val] = self.operands
        print("load %s %s" % (val.type, val.get_reference()), file=buf)


class StoreInstr(Instruction):
    def __init__(self, parent, val, ptr):
        super(StoreInstr, self).__init__(parent, lltypes.VoidType(), "store",
                                         [val, ptr])

    def descr(self, buf):
        val, ptr = self.operands
        print("store %s %s, %s %s" % (val.type, val.get_reference(),
                                      ptr.type, ptr.get_reference()), file=buf)


class AllocaInstr(Instruction):
    def __init__(self, parent, typ, count, name):
        operands = [count] if count else ()
        super(AllocaInstr, self).__init__(parent, typ.as_pointer(), "alloca",
                                          operands, name)

    def descr(self, buf):
        print("%s %s" % (self.opname, self.type.pointee), file=buf, end='')
        if self.operands:
            print(", %s %s" % (self.operands[0].type,
                               self.operands[0].get_reference()), file=buf)

