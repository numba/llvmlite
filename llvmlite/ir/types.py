"""
Classes that are LLVM types
"""

from __future__ import print_function, absolute_import

_type_state = iter(range(50))
_type_enum = lambda: next(_type_state)

TYPE_UNKNOWN = _type_enum()
TYPE_POINTER = _type_enum()
TYPE_STRUCT = _type_enum()
TYPE_METADATA = _type_enum()


class Type(object):
    is_pointer = False

    kind = TYPE_UNKNOWN

    def __repr__(self):
        return "<%s %s>" % (type(self), str(self))

    def __str__(self):
        raise NotImplementedError

    def as_pointer(self):
        return PointerType(self)

    def __ne__(self, other):
        return not (self == other)


class MetaData(object):
    kind = TYPE_METADATA

    def __str__(self):
        return "metadata"

    def as_pointer(self):
        raise TypeError


class LabelType(Type):
    def __str__(self):
        return "label"

    def __eq__(self, other):
        return isinstance(other, VoidType)


class PointerType(Type):
    is_pointer = True
    kind = TYPE_POINTER
    null = 'null'

    def __init__(self, pointee):
        assert not isinstance(pointee, VoidType)
        self.pointee = pointee

    def __str__(self):
        return "%s*" % (self.pointee, )

    def __eq__(self, other):
        if isinstance(other, PointerType):
            return self.pointee == other.pointee
        else:
            return False

    def gep(self, i):
        return self.pointee


class VoidType(Type):
    def __str__(self):
        return 'void'

    def __eq__(self, other):
        return isinstance(other, VoidType)


class FunctionType(Type):
    def __init__(self, return_type, args, var_arg=False):
        self.return_type = return_type
        self.args = tuple(args)
        self.var_arg = var_arg

    def __str__(self):
        strargs = ', '.join(str(a) for a in self.args)
        if self.var_arg:
            return '{0} ({1}, ...)'.format(self.return_type, strargs)
        else:
            return '{0} ({1})'.format(self.return_type, strargs)

    def __eq__(self, other):
        if isinstance(other, FunctionType):
            return (self.return_type == other.return_type and
                    all((a == b) for a, b in zip(self.args, other.args)))
        else:
            return False


class IntType(Type):
    null = '0'

    def __init__(self, bits):
        self.width = int(bits)

    def __str__(self):
        return 'i%u' % (self.width,)

    def __eq__(self, other):
        if isinstance(other, IntType):
            return self.width == other.width
        else:
            return False

class FloatType(Type):
    null = '0.0'

    def __str__(self):
        return 'float'


class DoubleType(Type):
    def __str__(self):
        return 'double'


class _Repeat(object):
    def __init__(self, value, size):
        self.value = value
        self.size = size

    def __len__(self):
        return self.size

    def __getitem__(self, item):
        if 0 <= item < self.size:
            return self.value
        else:
            raise IndexError(item)


class ArrayType(Type):
    def __init__(self, element, count):
        self.element = element
        self.count = count

    @property
    def elements(self):
        return _Repeat(self.element, self.count)

    def __len__(self):
        return self.count

    def __str__(self):
        return '[{0:d} x {1}]'.format(self.count, self.element)

    def __eq__(self, other):
        if isinstance(other, ArrayType):
            return self.element == other.element and self.count == other.count

    def gep(self, i):
        return self.element


class StructType(Type):
    kind = TYPE_STRUCT

    def __len__(self):
        assert not self.is_opaque
        return len(self.elements)

    def __iter__(self):
        assert not self.is_opaque
        return iter(self.elements)

    @property
    def is_opaque(self):
        return self.elements is None


class LiteralStructType(StructType):
    def __init__(self, elems):
        self.elements = tuple(elems)

    def __str__(self):
        return '{%s}' % ', '.join(map(str, self.elements))

    def __eq__(self, other):
        if isinstance(other, LiteralStructType):
            return self.elements == other.elements

    def gep(self, i):
        if not isinstance(i.type, IntType):
            raise TypeError(i.type)
        return self.elements[i.constant]


class IdentifiedStructType(StructType):
    def __init__(self, context, name):
        """Do not use this directly
        """
        assert name
        self.context = context
        self.name = name
        self.elements = None

    def __str__(self):
        return '%%%s' % self.name

    def __eq__(self, other):
        if isinstance(other, IdentifiedStructType):
            return self.name == other.name



