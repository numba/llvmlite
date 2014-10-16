from llvmlite import ir
from llvmlite import binding as llvm

CallOrInvokeInstruction = ir.CallInstr


class LLVMException(Exception):
    pass


_icmp_ct = iter(range(40))
_icmp_get = lambda: next(_icmp_ct)

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

TYPE_STRUCT = ir.TYPE_STRUCT
TYPE_POINTER = ir.TYPE_POINTER

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
    def double():
        return ir.DoubleType()

    @staticmethod
    def pointer(ty):
        return ir.PointerType(ty)

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
        text = r"{0}\00".format(repr(string)[1:-1])
        n = len(string) + 1
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), text)

    @staticmethod
    def array(typ, val):
        return ir.Constant(ir.ArrayType(typ, len(val)), val)

    @staticmethod
    def bitcast(const, typ):
        return const.bitcast(typ)

    @staticmethod
    def inttoptr(const, typ):
        return const.inttoptr(typ)


class Module(ir.Module):
    @classmethod
    def new(cls, name=''):
        return cls(name=name)

    def get_or_insert_function(self, fnty, name):
        if name in self.globals:
            return self.globals[name]
        else:
            return ir.Function(self, fnty, name)

    def verify(self):
        llvm.parse_assembly(str(self))

    def add_function(self, fnty, name):
        return ir.Function(self, fnty, name)

    def add_global_variable(self, ty, name):
        return ir.GlobalVariable(self, ty, self.get_unique_name(name))

    def get_global_variable_named(self, name):
        try:
            return self.globals[name]
        except KeyError:
            raise LLVMException(name)


class Builder(ir.IRBuilder):
    @classmethod
    def new(cls, bb):
        return cls(bb)

    def icmp(self, pred, lhs, rhs, name=''):
        umap = {ICMP_EQ: '==',
                ICMP_NE: '!=',
                ICMP_ULT: '<',
                ICMP_ULE: '<=',
                ICMP_UGT: '>',
                ICMP_UGE: '>='}

        smap = {ICMP_SLT: '<',
                ICMP_SLE: '<=',
                ICMP_SGT: '>',
                ICMP_SGE: '>='}

        if pred in umap:
            return self.icmp_unsigned(umap[pred], lhs, rhs, name=name)
        else:
            return self.icmp_signed(smap[pred], lhs, rhs, name=name)

    def fcmp(self, pred, lhs, rhs, name=''):
        omap = {FCMP_OEQ: '==',
                FCMP_OGT: '>',
                FCMP_OGE: '>=',
                FCMP_OLT: '<',
                FCMP_OLE: '<=',
                FCMP_ONE: '!=',
                FCMP_ORD: 'ord'}

        umap = {FCMP_UEQ: '==',
                FCMP_UGT: '>',
                FCMP_UGE: '>=',
                FCMP_ULT: '<',
                FCMP_ULE: '<=',
                FCMP_UNE: '!=',
                FCMP_UNO: 'uno'}

        if pred in umap:
            return self.fcmp_unordered(umap[pred], lhs, rhs, name=name)
        else:
            return self.fcmp_ordered(omap[pred], lhs, rhs, name=name)

    def switch(self, val, elseblk, n):
        """
        n is ignored
        """
        return super(Builder, self).switch(val, elseblk)


class MetaDataString(ir.MetaDataString):
    @staticmethod
    def get(module, text):
        return MetaDataString(module, text)


class MetaData(ir.MetaData):
    @staticmethod
    def get(module, values):
        return module.add_metadata(values)
