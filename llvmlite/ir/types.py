"""
Classes that are LLVM types
"""

from __future__ import print_function, absolute_import

import struct


# XXX This doesn't seem to be used
_type_state = iter(range(50))
_type_enum = lambda: next(_type_state)

TYPE_UNKNOWN = _type_enum()
TYPE_POINTER = _type_enum()
TYPE_STRUCT = _type_enum()
TYPE_METADATA = _type_enum()


class Type(object):
    """
    The base class for all LLVM types.
    """
    is_pointer = False
    null = 'zeroinitializer'

    kind = TYPE_UNKNOWN

    def __repr__(self):
        return "<%s %s>" % (type(self), str(self))

    def __str__(self):
        raise NotImplementedError

    def as_pointer(self, addrspace=0):
        return PointerType(self, addrspace)

    def __ne__(self, other):
        return not (self == other)

    def get_abi_size(self, target_data):
        """
        Get the ABI size of this type according to data layout *target_data*.
        """
        from . import Module, GlobalVariable
        from ..binding import parse_assembly

        # We need to convert our type object to an LLVM type
        m = Module()
        foo = GlobalVariable(m, self, name="foo")
        with parse_assembly(str(m)) as llmod:
            llty = llmod.get_global_variable(foo.name).type
            return target_data.get_pointee_abi_size(llty)

    def format_const(self, val):
        """
        Format constant *val* of this type.  This method may be overriden
        by subclasses.
        """
        return str(val)


class MetaData(Type):
    kind = TYPE_METADATA

    def __str__(self):
        return "metadata"

    def as_pointer(self):
        raise TypeError


class LabelType(Type):
    """
    The label type is the type of e.g. basic blocks.
    """

    def __str__(self):
        return "label"


class PointerType(Type):
    """
    The type of all pointer values.
    """
    is_pointer = True
    kind = TYPE_POINTER
    null = 'null'

    def __init__(self, pointee, addrspace=0):
        assert not isinstance(pointee, VoidType)
        self.pointee = pointee
        self.addrspace = addrspace

    def __str__(self):
        if self.addrspace != 0:
            return "{0} addrspace({1})* ".format(self.pointee, self.addrspace)
        else:
            return "{0}*".format(self.pointee)

    def __eq__(self, other):
        if isinstance(other, PointerType):
            return (self.pointee, self.addrspace) == (other.pointee,
                                                      other.addrspace)
        else:
            return False

    def gep(self, i):
        """
        Resolve the type of the i-th element (for getelementptr lookups).
        """
        if not isinstance(i.type, IntType):
            raise TypeError(i.type)
        return self.pointee


class VoidType(Type):
    """
    The type for empty values (e.g. a function returning no value).
    """

    def __str__(self):
        return 'void'

    def __eq__(self, other):
        return isinstance(other, VoidType)


class FunctionType(Type):
    """
    The type for functions.
    """

    def __init__(self, return_type, args, var_arg=False):
        self.return_type = return_type
        self.args = tuple(args)
        self.var_arg = var_arg

    def __str__(self):
        if self.args:
            strargs = ', '.join(str(a) for a in self.args)
            if self.var_arg:
                return '{0} ({1}, ...)'.format(self.return_type, strargs)
            else:
                return '{0} ({1})'.format(self.return_type, strargs)
        elif self.var_arg:
            return '{0} (...)'.format(self.return_type)
        else:
            return '{0} ()'.format(self.return_type)

    def __eq__(self, other):
        if isinstance(other, FunctionType):
            return (self.return_type == other.return_type and
                    self.args == other.args and self.var_arg == other.var_arg)
        else:
            return False


class IntType(Type):
    """
    The type for integers.
    """
    null = '0'

    def __init__(self, bits):
        assert isinstance(bits, int)
        self.width = bits

    def __str__(self):
        return 'i%u' % (self.width,)

    def __eq__(self, other):
        if isinstance(other, IntType):
            return self.width == other.width
        else:
            return False

    def format_const(self, val):
        if isinstance(val, bool):
            return str(val).lower()
        else:
            return str(val)


def _as_float(value):
    """
    Truncate to single-precision float.
    """
    return struct.unpack('f', struct.pack('f', value))[0]

def _format_float_as_hex(value, packfmt, unpackfmt, numdigits):
    raw = struct.pack(packfmt, float(value))
    intrep = struct.unpack(unpackfmt, raw)[0]
    out = '{{0:#{0}x}}'.format(numdigits).format(intrep)
    return out

def _format_double(value):
    """
    Format *value* as a hexadecimal string of its IEEE double precision
    representation.
    """
    return _format_float_as_hex(value, 'd', 'Q', 16)


class FloatType(Type):
    """
    The type for single-precision floats.
    """
    null = '0.0'
    intrinsic_name = 'f32'

    def __str__(self):
        return 'float'

    def __eq__(self, other):
        return isinstance(other, type(self))

    def format_const(self, val):
        return _format_double(_as_float(val))


class DoubleType(Type):
    """
    The type for double-precision floats.
    """
    null = '0.0'
    intrinsic_name = 'f64'

    def __str__(self):
        return 'double'

    def __eq__(self, other):
        return isinstance(other, type(self))

    def format_const(self, val):
        return _format_double(val)


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


class Aggregate(Type):
    """
    Base class for aggregate types.
    See http://llvm.org/docs/LangRef.html#t-aggregate
    """


class ArrayType(Aggregate):
    """
    The type for fixed-size homogenous arrays (e.g. "[f32 x 3]").
    """

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
        """
        Resolve the type of the i-th element (for getelementptr lookups).
        """
        if not isinstance(i.type, IntType):
            raise TypeError(i.type)
        return self.element

    def format_const(self, val):
        fmter = lambda x: "{0} {1}".format(x.type, x.get_reference())
        return "[{0}]".format(', '.join(map(fmter, val)))


class BaseStructType(Aggregate):
    """
    The base type for heterogenous struct types.
    """

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

    def structure_repr(self):
        """Return the LLVM IR for the structure representation
        """
        return '{%s}' % ', '.join(map(str, self.elements))

    def format_const(self, val):
        fmter = lambda x: "{0} {1}".format(x.type, x.get_reference())
        return "{{{0}}}".format(', '.join(map(fmter, val)))


class LiteralStructType(BaseStructType):
    """
    The type of "literal" structs, i.e. structs with a literally-defined
    type (by contrast with IdentifiedStructType).
    """

    null = 'zeroinitializer'

    def __init__(self, elems):
        self.elements = tuple(elems)

    def __str__(self):
        return self.structure_repr()

    def __eq__(self, other):
        if isinstance(other, LiteralStructType):
            return self.elements == other.elements

    def gep(self, i):
        """
        Resolve the type of the i-th element (for getelementptr lookups).

        *i* needs to be a LLVM constant, so that the type can be determined
        at compile-time.
        """
        if not isinstance(i.type, IntType):
            raise TypeError(i.type)
        return self.elements[i.constant]


class IdentifiedStructType(BaseStructType):
    """
    A type which is a named alias for another struct type, akin to a typedef.
    While literal struct types can be structurally equal (see
    LiteralStructType), identified struct types are compared by name.

    Do not use this directly.
    """
    null = 'zeroinitializer'

    def __init__(self, context, name):
        assert name
        self.context = context
        self.name = name
        self.elements = None

    def __str__(self):
        return "%{name}".format(name=self.name)

    def get_declaration(self):
        """Returns the string for the declaration of the type
        """
        if self.is_opaque:
            out = "{strrep} = type opaque".format(strrep=str(self))
        else:
            out = "{strrep} = type {struct}".format(
                strrep=str(self), struct=self.structure_repr())
        return out

    def __eq__(self, other):
        if isinstance(other, IdentifiedStructType):
            return self.name == other.name

    def set_body(self, *elems):
        if not self.is_opaque:
            raise RuntimeError("{name} is already defined".format(
                name=self.name))
        self.elements = tuple(elems)
