"""
Classes that are LLVM values: Value, Constant...
Instructions are in the instructions module.
"""

from __future__ import print_function, absolute_import

import string

from ..six import StringIO
from . import types

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


class _Undefined(object):
    pass

Undefined = _Undefined()


def _wrapname(x):
    return '"{0}"'.format(x).replace(' ', '_')


class ConstOp(object):
    def __init__(self, typ, op):
        self.type = typ
        self.op = op

    def __str__(self):
        return "{0}".format(self.op)

    def get_reference(self):
        return str(self)


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

    def gep(self, indices):
        assert isinstance(self.type, types.PointerType)

        outtype = self.type
        for i in indices:
            outtype = outtype.gep(i)

        strindices = ["{0} {1}".format(idx.type, idx.get_reference())
                      for idx in indices]

        op = "getelementptr ({0} {1}, {2})".format(self.type,
                                                   self.get_reference(),
                                                   ', '.join(strindices))
        return ConstOp(outtype.as_pointer(), op)


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

        else:
            val = self.type.format_const(self.constant)

        return val

    @classmethod
    def literal_struct(cls, elems):
        tys = [el.type for el in elems]
        return cls(types.LiteralStructType(tys), elems)

    def __eq__(self, other):
        if isinstance(other, Constant):
            return str(self) == str(other)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))


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

    def __str__(self):
        buf = StringIO()
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

    @property
    def function_type(self):
        ty = self.type
        if isinstance(ty, types.PointerType):
            ty = self.type.pointee
        if isinstance(ty, types.FunctionType):
            return ty
        else:
            raise TypeError("Not a function: {0}".format(self.type))


class MetaDataString(Value):
    """
    A metadata string, i.e. a constant string used as a value in a metadata
    node.
    """

    def __init__(self, parent, string):
        super(MetaDataString, self).__init__(parent, types.MetaData(), name="")
        self.string = string

    def descr(self, buf):
        print("metadata !\"{0}\"".format(self.string), file=buf)

    def get_reference(self):
        return "!\"{0}\"".format(self.string)

    def __str__(self):
        return self.get_reference()

    def __eq__(self, other):
        if isinstance(other, MetaDataString):
            return self.string == other.string
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.string)


class NamedMetaData(object):
    name_prefix = '!'

    def __init__(self, parent):
        self.parent = parent
        self.operands = []

    def add(self, md):
        self.operands.append(md)


class MDValue(Value):
    name_prefix = '!'

    def __init__(self, parent, values, name):
        super(MDValue, self).__init__(parent, types.MetaData(), name=name)
        self.operands = tuple(values)
        parent.metadata.append(self)

    @property
    def operand_count(self):
        return len(self.operands)

    def descr(self, buf):
        operands = ', '.join("{0} {1}".format(op.type, op.get_reference())
                             for op in self.operands)
        print("metadata !{{ {operands} }}".format(operands=operands), file=buf)

    def get_reference(self):
        return self.name_prefix + str(self.name)

    def __eq__(self, other):
        if isinstance(other, MDValue):
            return self.operands == other.operands
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.operands)


class GlobalValue(Value, ConstOpMixin):
    name_prefix = '@'
    deduplicate_name = False

    def __init__(self, *args, **kwargs):
        super(GlobalValue, self).__init__(*args, **kwargs)
        self.linkage = ''


class GlobalVariable(GlobalValue):
    def __init__(self, module, typ, name, addrspace=0):
        super(GlobalVariable, self).__init__(module, typ.as_pointer(addrspace),
                                             name=name)
        self.gtype = typ
        self.initializer = None
        self.global_constant = False
        self.addrspace = addrspace
        self.parent.add_global(self)

    def descr(self, buf):
        if self.global_constant:
            kind = 'constant'
        else:
            kind = 'global'

        if not self.linkage:
            # Default to external linkage
            linkage = 'external' if self.initializer is None else ''
        else:
            linkage = self.linkage

        if self.addrspace != 0:
            addrspace = 'addrspace({0:d})'.format(self.addrspace)
        else:
            addrspace = ''

        print("{linkage} {addrspace} {kind} {type} ".format(
            addrspace=addrspace,
            linkage=linkage,
            kind=kind,
            type=self.gtype),
              file=buf,
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
        attrs = sorted(self)
        if self.alignstack:
            attrs.append('alignstack({0:d})'.format(self.alignstack))
        return ' '.join(attrs)


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
        self.calling_convention = ''

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
        cconv = self.calling_convention
        prefix = " ".join(str(x) for x in [state, linkage, cconv, retty] if x)
        prototype = "{prefix} {name}({args}{vararg}) {attrs}".format(**locals())
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
        buf = StringIO()
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
        if self.attributes:
            return "{0} {1} {2}".format(self.type, ' '.join(self.attributes),
                                        self.get_reference())
        else:
            return "{0} {1}".format(self.type, self.get_reference())

    def __repr__(self):
        return "<Argument %r (#%s) of type %s>" % (self.name, self.pos, self.type)

    def add_attribute(self, attr):
        self.attributes.add(attr)


class Block(Value):
    """
    A LLVM IR building block. A building block is a sequence of
    instructions whose execution always goes from start to end.  That
    is, a control flow instruction (branch) can only appear as the
    last instruction, and incoming branches can only jump to the first
    instruction.
    """

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

    def replace(self, old, new):
        """Replace an instruction"""
        if old.type != new.type:
            raise TypeError("new instruction has a different type")
        pos = self.instructions.index(old)
        self.instructions.remove(old)
        self.instructions.insert(pos, new)

        for bb in self.parent.basic_blocks:
            for instr in bb.instructions:
                instr.replace_usage(old, new)

