"""
Classes that are LLVM values: Value, Constant...
Instructions are in the instructions module.
"""

from __future__ import print_function, absolute_import

import string

from ..six import StringIO
from . import types
from ._utils import _StrCaching, _StringReferenceCaching


_VALID_CHARS = (frozenset(map(ord, string.ascii_letters)) |
                frozenset(map(ord, string.digits)) |
                frozenset('._-$'))


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


class ConstOp(object):
    """
    A simple value-like object representing the result of a constant operation.
    """

    def __init__(self, typ, op):
        assert isinstance(typ, types.Type)
        self.type = typ
        self.op = op

    def __str__(self):
        return self.op

    get_reference = __str__


class ConstOpMixin(object):
    """
    A mixin defining constant operations, for use in constant-like classes.
    """

    def bitcast(self, typ):
        """
        Bitcast this pointer constant to the given type.
        """
        if typ == self.type:
            return self
        op = "bitcast ({0} {1} to {2})".format(self.type, self.get_reference(),
                                               typ)
        return ConstOp(typ, op)

    def inttoptr(self, typ):
        """
        Cast this integer constant to the given pointer type.
        """
        assert isinstance(self.type, types.IntType)
        assert isinstance(typ, types.PointerType)
        op = "inttoptr ({0} {1} to {2})".format(self.type,
                                                self.get_reference(),
                                                typ)
        return ConstOp(typ, op)

    def gep(self, indices):
        """
        Call getelementptr on this pointer constant.
        """
        if not isinstance(self.type, types.PointerType):
            raise TypeError("cannot only call gep() on pointer constants")

        outtype = self.type
        for i in indices:
            outtype = outtype.gep(i)

        strindices = ["{0} {1}".format(idx.type, idx.get_reference())
                      for idx in indices]

        op = "getelementptr ({0}, {1} {2}, {3})".format(
            self.type.pointee, self.type,
            self.get_reference(), ', '.join(strindices))
        return ConstOp(outtype.as_pointer(), op)


class Constant(_StrCaching, _StringReferenceCaching, ConstOpMixin):
    """
    A constant LLVM value.
    """

    def __init__(self, typ, constant):
        assert isinstance(typ, types.Type)
        assert not isinstance(typ, types.VoidType)
        self.type = typ
        self.constant = constant

    def _to_string(self):
        return '{0} {1}'.format(self.type, self.get_reference())

    def _get_reference(self):
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
        """
        Construct a literal structure constant made of the given members.
        """
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


class Value(_StrCaching, _StringReferenceCaching):
    name_prefix = '%'
    deduplicate_name = True
    creates_nested_scope = False

    def __init__(self, parent, type, name):
        assert parent is not None
        assert isinstance(type, types.Type)
        self.parent = parent
        self.type = type
        pscope = self.parent.scope
        self.scope = pscope.get_child() if self.creates_nested_scope else pscope
        self._set_name(name)

    def _to_string(self):
        buf = []
        if self.type != types.VoidType():
            buf.append("{0} = ".format(self.get_reference()))
        self.descr(buf)
        return "".join(buf).rstrip()

    def descr(self, buf):
        raise NotImplementedError

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        name = self.scope.register(name, deduplicate=self.deduplicate_name)
        self._name = name

    name = property(_get_name, _set_name)

    def _get_reference(self):
        name = self.name
        # Quote and escape value name
        if '\\' in name or '"' in name:
            name = name.replace('\\', '\\5c').replace('"', '\\22')
        return '{0}"{1}"'.format(self.name_prefix, name)

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
        buf += (self.get_reference(), "\n")

    def _get_reference(self):
        return '!"{0}"'.format(self.string)

    _to_string = _get_reference

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
        operands = []
        for op in self.operands:
            typestr = str(op.type)
            if isinstance(op.type, types.MetaData):
                operands.append(op.get_reference())
            else:
                operands.append("{0} {1}".format(op.type, op.get_reference()))
        operands = ', '.join(operands)
        buf += ("!{{ {0} }}".format(operands), "\n")

    def _get_reference(self):
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
    """
    A global value.
    """
    name_prefix = '@'
    deduplicate_name = False

    def __init__(self, *args, **kwargs):
        super(GlobalValue, self).__init__(*args, **kwargs)
        self.linkage = ''
        self.storage_class = ''


class GlobalVariable(GlobalValue):
    """
    A global variable.
    """

    def __init__(self, module, typ, name, addrspace=0):
        assert isinstance(typ, types.Type)
        super(GlobalVariable, self).__init__(module, typ.as_pointer(addrspace),
                                             name=name)
        self.gtype = typ
        self.initializer = None
        self.unnamed_addr = False
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

        if self.unnamed_addr:
            unnamed_addr = 'unnamed_addr'
        else:
            unnamed_addr = ''

        buf.append("{linkage} {storage_class} {unnamed_addr} {addrspace} {kind} {type} "
                   .format(linkage=linkage,
                           storage_class=self.storage_class,
                           unnamed_addr=unnamed_addr,
                           addrspace=addrspace,
                           kind=kind,
                           type=self.gtype))

        if self.initializer is not None:
            buf.append(self.initializer.get_reference())
        buf.append("\n")


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
    creates_nested_scope = True

    def __init__(self, module, ftype, name):
        assert isinstance(ftype, types.Type)
        super(Function, self).__init__(module, ftype.as_pointer(), name=name)
        self.ftype = ftype
        self.blocks = []
        self.attributes = FunctionAttributes()
        self.args = tuple([Argument(self, t)
                           for t in ftype.args])
        self.return_value = ReturnValue(self, ftype.return_type)
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
        ret = self.return_value
        args = ", ".join(str(a) for a in self.args)
        name = self.get_reference()
        attrs = self.attributes
        if any(self.args):
            vararg = ', ...' if self.ftype.var_arg else ''
        else:
            vararg = '...' if self.ftype.var_arg else ''
        linkage = self.linkage
        cconv = self.calling_convention
        prefix = " ".join(str(x) for x in [state, linkage, cconv, ret] if x)
        prototype = "{prefix} {name}({args}{vararg}) {attrs}\n".format(**locals())
        buf.append(prototype)

    def descr_body(self, buf):
        """
        Describe of the body of the function.
        """
        for blk in self.blocks:
            blk.descr(buf)

    def descr(self, buf):
        self.descr_prototype(buf)
        if self.blocks:
            buf.append("{\n")
            self.descr_body(buf)
            buf.append("}\n")

    def __str__(self):
        buf = []
        self.descr(buf)
        return "".join(buf)

    @property
    def is_declaration(self):
        return len(self.blocks) == 0


class ArgumentAttributes(AttributeSet):
    _known = frozenset(['byval', 'inalloca', 'inreg', 'nest', 'noalias',
                        'nocapture', 'nonnull', 'returned', 'signext',
                        'sret', 'zeroext'])


class _BaseArgument(Value):
    def __init__(self, parent, typ, name=''):
        assert isinstance(typ, types.Type)
        super(_BaseArgument, self).__init__(parent, typ, name=name)
        self.parent = parent
        self.attributes = ArgumentAttributes()

    def __repr__(self):
        return "<Argument %r of type %s>" % (self.name, self.type)

    def add_attribute(self, attr):
        self.attributes.add(attr)


class Argument(_BaseArgument):
    """
    The specification of a function argument.
    """

    def __str__(self):
        if self.attributes:
            return "{0} {1} {2}".format(self.type, ' '.join(self.attributes),
                                        self.get_reference())
        else:
            return "{0} {1}".format(self.type, self.get_reference())


class ReturnValue(_BaseArgument):
    """
    The specification of a function's return value.
    """

    def __str__(self):
        if self.attributes:
            return "{0} {1}".format(' '.join(self.attributes), self.type)
        else:
            return str(self.type)


class Block(Value):
    """
    A LLVM IR basic block. A basic block is a sequence of
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
        buf.append("{0}:\n".format(self.name))
        buf += ["  {0}\n".format(instr) for instr in self.instructions]

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


class BlockAddress(object):
    """
    The address of a basic block.
    """

    def __init__(self, function, basic_block):
        assert isinstance(function, Function)
        assert isinstance(basic_block, Block)
        self.type = types.IntType(8).as_pointer()
        self.function = function
        self.basic_block = basic_block

    def __str__(self):
        return '{0} {1}'.format(self.type, self.get_reference())

    def get_reference(self):
        return "blockaddress({0}, {1})".format(
                    self.function.get_reference(),
                    self.basic_block.get_reference())
