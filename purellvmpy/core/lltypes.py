from __future__ import print_function, absolute_import


class Type(object):
    is_pointer = False

    def __repr__(self):
        return "<%s %s>" % (type(self), str(self))

    def __str__(self):
        raise NotImplementedError

    def as_pointer(self):
        return PointerType(self)

    def __ne__(self, other):
        return not (self == other)


class LabelType(Type):
    def __str__(self):
        return "label"

    def __eq__(self, other):
        return isinstance(other, VoidType)


class PointerType(Type):
    is_pointer = True

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


class VoidType(Type):
    def __str__(self):
        return 'void'

    def __eq__(self, other):
        return isinstance(other, VoidType)


class FunctionType(Type):
    def __init__(self, return_type, *args):
        self.return_type = return_type
        self.args = args

    def __str__(self):
        strargs = ', '.join(str(a) for a in self.args)
        return '%s (%s)' % (self.return_type, strargs)

    def __eq__(self, other):
        if isinstance(other, FunctionType):
            return (self.return_type == other.return_type and
                    all((a == b) for a, b in zip(self.args, other.args)))
        else:
            return False


class IntType(Type):
    def __init__(self, bits):
        self.bits = bits

    def __str__(self):
        return 'i%u' % (self.bits,)

    def __eq__(self, other):
        if isinstance(other, IntType):
            return self.bits == other.bits
        else:
            return False

