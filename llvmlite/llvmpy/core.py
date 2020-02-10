import itertools

from llvmlite import ir
from llvmlite import binding as llvm

CallOrInvokeInstruction = ir.CallInstr


class LLVMException(Exception):
    pass


_icmp_ct = itertools.count()


def _icmp_get():
    return next(_icmp_ct)


ICMP_EQ = _icmp_get()
ICMP_NE = _icmp_get()
ICMP_SLT = _icmp_get()
ICMP_SLE = _icmp_get()
ICMP_SGT = _icmp_get()
ICMP_SGE = _icmp_get()
ICMP_ULT = _icmp_get()
ICMP_ULE = _icmp_get()
ICMP_UGT = _icmp_get()
ICMP_UGE = _icmp_get()

FCMP_OEQ = _icmp_get()
FCMP_OGT = _icmp_get()
FCMP_OGE = _icmp_get()
FCMP_OLT = _icmp_get()
FCMP_OLE = _icmp_get()
FCMP_ONE = _icmp_get()
FCMP_ORD = _icmp_get()

FCMP_UEQ = _icmp_get()
FCMP_UGT = _icmp_get()
FCMP_UGE = _icmp_get()
FCMP_ULT = _icmp_get()
FCMP_ULE = _icmp_get()
FCMP_UNE = _icmp_get()
FCMP_UNO = _icmp_get()

INTR_FABS = "llvm.fabs"
INTR_EXP = "llvm.exp"
INTR_LOG = "llvm.log"
INTR_LOG10 = "llvm.log10"
INTR_SIN = "llvm.sin"
INTR_COS = "llvm.cos"
INTR_POWI = 'llvm.powi'
INTR_POW = 'llvm.pow'
INTR_FLOOR = 'llvm.floor'

LINKAGE_EXTERNAL = 'external'
LINKAGE_INTERNAL = 'internal'
LINKAGE_LINKONCE_ODR = 'linkonce_odr'

ATTR_NO_CAPTURE = 'nocapture'


class Type(object):
    @staticmethod
    def int(width=32):
        return ir.IntType(width)

    @staticmethod
    def float():
        return ir.FloatType()

    @staticmethod
    def half():
        return ir.HalfType()

    @staticmethod
    def double():
        return ir.DoubleType()

    @staticmethod
    def pointer(ty, addrspace=0):
        return ir.PointerType(ty, addrspace)

    @staticmethod
    def function(res, args, var_arg=False):
        return ir.FunctionType(res, args, var_arg=var_arg)

    @staticmethod
    def struct(members):
        return ir.LiteralStructType(members)

    @staticmethod
    def array(element, count):
        return ir.ArrayType(element, count)

    @staticmethod
    def void():
        return ir.VoidType()


class Constant(object):
    @staticmethod
    def all_ones(ty):
        if isinstance(ty, ir.IntType):
            return Constant.int(ty, int('1' * ty.width, 2))
        else:
            raise NotImplementedError(ty)

    @staticmethod
    def int(ty, n):
        return ir.Constant(ty, n)

    @staticmethod
    def int_signextend(ty, n):
        return ir.Constant(ty, n)

    @staticmethod
    def real(ty, n):
        return ir.Constant(ty, n)

    @staticmethod
    def struct(elems):
        return ir.Constant.literal_struct(elems)

    @staticmethod
    def null(ty):
        return ir.Constant(ty, None)

    @staticmethod
    def undef(ty):
        return ir.Constant(ty, ir.Undefined)

    @staticmethod
    def stringz(string):
        n = (len(string) + 1)
        buf = bytearray((' ' * n).encode('ascii'))
        buf[-1] = 0
        buf[:-1] = string.encode('utf-8')
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), buf)

    @staticmethod
    def array(typ, val):
        return ir.Constant(ir.ArrayType(typ, len(val)), val)

    @staticmethod
    def bitcast(const, typ):
        return const.bitcast(typ)

    @staticmethod
    def inttoptr(const, typ):
        return const.inttoptr(typ)

    @staticmethod
    def gep(const, indices):
        return const.gep(indices)


class Module(ir.Module):

    def get_or_insert_function(self, fnty, name):
        if name in self.globals:
            return self.globals[name]
        else:
            return ir.Function(self, fnty, name)

    def verify(self):
        llvm.parse_assembly(str(self))

    def add_function(self, fnty, name):
        return ir.Function(self, fnty, name)

    def add_global_variable(self, ty, name, addrspace=0):
        return ir.GlobalVariable(self, ty, self.get_unique_name(name),
                                 addrspace)

    def get_global_variable_named(self, name):
        try:
            return self.globals[name]
        except KeyError:
            raise LLVMException(name)

    def get_or_insert_named_metadata(self, name):
        try:
            return self.get_named_metadata(name)
        except KeyError:
            return self.add_named_metadata(name)


class Function(ir.Function):

    @classmethod
    def new(cls, module_obj, functy, name=''):
        return cls(module_obj, functy, name)

    @staticmethod
    def intrinsic(module, intrinsic, tys):
        return module.declare_intrinsic(intrinsic, tys)


_icmp_umap = {
    ICMP_EQ: '==',
    ICMP_NE: '!=',
    ICMP_ULT: '<',
    ICMP_ULE: '<=',
    ICMP_UGT: '>',
    ICMP_UGE: '>=',
}

_icmp_smap = {
    ICMP_SLT: '<',
    ICMP_SLE: '<=',
    ICMP_SGT: '>',
    ICMP_SGE: '>=',
}

_fcmp_omap = {
    FCMP_OEQ: '==',
    FCMP_OGT: '>',
    FCMP_OGE: '>=',
    FCMP_OLT: '<',
    FCMP_OLE: '<=',
    FCMP_ONE: '!=',
    FCMP_ORD: 'ord',
}

_fcmp_umap = {
    FCMP_UEQ: '==',
    FCMP_UGT: '>',
    FCMP_UGE: '>=',
    FCMP_ULT: '<',
    FCMP_ULE: '<=',
    FCMP_UNE: '!=',
    FCMP_UNO: 'uno',
}


class Builder(ir.IRBuilder):

    def icmp(self, pred, lhs, rhs, name=''):
        if pred in _icmp_umap:
            return self.icmp_unsigned(_icmp_umap[pred], lhs, rhs, name=name)
        else:
            return self.icmp_signed(_icmp_smap[pred], lhs, rhs, name=name)

    def fcmp(self, pred, lhs, rhs, name=''):
        if pred in _fcmp_umap:
            return self.fcmp_unordered(_fcmp_umap[pred], lhs, rhs, name=name)
        else:
            return self.fcmp_ordered(_fcmp_omap[pred], lhs, rhs, name=name)


class MetaDataString(ir.MetaDataString):
    @staticmethod
    def get(module, text):
        return MetaDataString(module, text)


class MetaData(object):
    @staticmethod
    def get(module, values):
        return module.add_metadata(values)


class InlineAsm(ir.InlineAsm):
    @staticmethod
    def get(*args, **kwargs):
        return InlineAsm(*args, **kwargs)
