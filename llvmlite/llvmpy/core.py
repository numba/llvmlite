from __future__ import annotations

import builtins
import itertools
import warnings
from typing import Iterable

from llvmlite import binding as llvm
from llvmlite import ir
from llvmlite.ir.instructions import FCMPInstr, ICMPInstr
from llvmlite.ir.values import GlobalVariable, MDValue, NamedMetaData

warnings.warn(
    "The module `llvmlite.llvmpy.core` is deprecated and will be removed in "
    "the future. Equivalent functionality is provided by `llvmlite.ir`."
)

CallOrInvokeInstruction = ir.CallInstr


class LLVMException(Exception):
    pass


_icmp_ct = itertools.count()


def _icmp_get() -> int:
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
INTR_POWI = "llvm.powi"
INTR_POW = "llvm.pow"
INTR_FLOOR = "llvm.floor"

LINKAGE_EXTERNAL = "external"
LINKAGE_INTERNAL = "internal"
LINKAGE_LINKONCE_ODR = "linkonce_odr"

ATTR_NO_CAPTURE = "nocapture"


class Type:
    @staticmethod
    def int(width: builtins.int = 32) -> ir.IntType:
        return ir.IntType(width)

    @staticmethod
    def float() -> ir.FloatType:
        return ir.FloatType()  # type: ignore

    @staticmethod
    def half() -> ir.HalfType:
        return ir.HalfType()  # type: ignore

    @staticmethod
    def double() -> ir.DoubleType:
        return ir.DoubleType()  # type: ignore

    @staticmethod
    def pointer(
        ty: ir.IntType | ir.PointerType | ir.FunctionType, addrspace: builtins.int = 0
    ) -> ir.PointerType:
        return ir.PointerType(ty, addrspace)

    @staticmethod
    def function(
        res: ir.Type, args: list[ir.Type], var_arg: bool = False
    ) -> ir.FunctionType:
        return ir.FunctionType(res, args, var_arg=var_arg)

    @staticmethod
    def struct(members: Iterable[ir.Type]) -> ir.LiteralStructType:
        return ir.LiteralStructType(members)

    @staticmethod
    def array(element: ir.Type, count: builtins.int) -> ir.ArrayType:
        return ir.ArrayType(element, count)

    @staticmethod
    def void() -> ir.VoidType:
        return ir.VoidType()


class Constant:
    @staticmethod
    def all_ones(ty: ir.IntType) -> ir.Constant:
        if isinstance(ty, ir.IntType):
            return Constant.int(ty, int("1" * ty.width, 2))
        else:
            raise NotImplementedError(ty)

    @staticmethod
    def int(ty: ir.Type, n: builtins.int) -> ir.Constant:
        return ir.Constant(ty, n)

    @staticmethod
    def int_signextend(ty: ir.Type, n: builtins.int) -> ir.Constant:
        return ir.Constant(ty, n)

    @staticmethod
    def real(ty: ir.Type, n: builtins.int) -> ir.Constant:
        return ir.Constant(ty, n)

    @staticmethod
    def struct(elems: list[ir.Constant]) -> ir.Constant:
        return ir.Constant.literal_struct(elems)

    @staticmethod
    def null(ty: ir.Type) -> ir.Constant:
        return ir.Constant(ty, None)

    @staticmethod
    def undef(ty: ir.Type) -> ir.Constant:
        return ir.Constant(ty, ir.Undefined)

    @staticmethod
    def stringz(string: str) -> ir.Constant:
        n = len(string) + 1
        buf = bytearray((" " * n).encode("ascii"))
        buf[-1] = 0
        buf[:-1] = string.encode("utf-8")
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), buf)

    @staticmethod
    def array(typ: ir.Type, val: list[ir.Constant]) -> ir.Constant:
        return ir.Constant(ir.ArrayType(typ, len(val)), val)

    @staticmethod
    def bitcast(const: ir.Constant, typ: ir.Type) -> ir.FormattedConstant:
        return const.bitcast(typ)  # type: ignore

    @staticmethod
    def inttoptr(const: ir.Constant, typ: ir.Type) -> ir.FormattedConstant:
        return const.inttoptr(typ)  # type: ignore

    @staticmethod
    def gep(const: ir.Constant, indices: list[ir.Constant]) -> ir.FormattedConstant:
        return const.gep(indices)


class Module(ir.Module):
    def get_or_insert_function(self, fnty: ir.FunctionType, name: str) -> ir.Function:
        if name in self.globals:
            return self.globals[name]  # type: ignore
        else:
            return ir.Function(self, fnty, name)

    def verify(self) -> None:
        llvm.parse_assembly(str(self))

    def add_function(self, fnty: ir.FunctionType, name: str) -> ir.Function:
        return ir.Function(self, fnty, name)

    def add_global_variable(
        self, ty: ir.Type, name: str, addrspace: builtins.int = 0
    ) -> ir.GlobalVariable:
        return ir.GlobalVariable(self, ty, self.get_unique_name(name), addrspace)

    def get_global_variable_named(self, name: str) -> ir.GlobalVariable:
        try:
            return self.globals[name]
        except KeyError:
            raise LLVMException(name)

    def get_or_insert_named_metadata(self, name: str) -> NamedMetaData:
        try:
            return self.get_named_metadata(name)
        except KeyError:
            return self.add_named_metadata(name)


class Function(ir.Function):
    @classmethod
    def new(
        cls, module_obj: Module, functy: ir.FunctionType, name: str = ""
    ) -> Function:
        return cls(module_obj, functy, name)

    @staticmethod
    def intrinsic(
        module: Module, intrinsic: str, tys: list[ir.Type]
    ) -> GlobalVariable | ir.Function:
        return module.declare_intrinsic(intrinsic, tys)


_icmp_umap = {
    ICMP_EQ: "==",
    ICMP_NE: "!=",
    ICMP_ULT: "<",
    ICMP_ULE: "<=",
    ICMP_UGT: ">",
    ICMP_UGE: ">=",
}

_icmp_smap = {
    ICMP_SLT: "<",
    ICMP_SLE: "<=",
    ICMP_SGT: ">",
    ICMP_SGE: ">=",
}

_fcmp_omap = {
    FCMP_OEQ: "==",
    FCMP_OGT: ">",
    FCMP_OGE: ">=",
    FCMP_OLT: "<",
    FCMP_OLE: "<=",
    FCMP_ONE: "!=",
    FCMP_ORD: "ord",
}

_fcmp_umap = {
    FCMP_UEQ: "==",
    FCMP_UGT: ">",
    FCMP_UGE: ">=",
    FCMP_ULT: "<",
    FCMP_ULE: "<=",
    FCMP_UNE: "!=",
    FCMP_UNO: "uno",
}


class Builder(ir.IRBuilder):
    def icmp(
        self, pred: str, lhs: ir.Constant, rhs: ir.Constant, name: str = ""
    ) -> ICMPInstr:
        if pred in _icmp_umap:
            return self.icmp_unsigned(_icmp_umap[pred], lhs, rhs, name=name)  # type: ignore
        else:
            return self.icmp_signed(_icmp_smap[pred], lhs, rhs, name=name)  # type: ignore

    def fcmp(
        self, pred: str, lhs: ir.Constant, rhs: ir.Constant, name: str = ""
    ) -> FCMPInstr:
        if pred in _fcmp_umap:
            return self.fcmp_unordered(_fcmp_umap[pred], lhs, rhs, name=name)  # type: ignore
        else:
            return self.fcmp_ordered(_fcmp_omap[pred], lhs, rhs, name=name)  # type: ignore


class MetaDataString(ir.MetaDataString):
    @staticmethod
    def get(module: Module, text: str) -> MetaDataString:
        return MetaDataString(module, text)


class MetaData:
    @staticmethod
    def get(module: Module, values: list[ir.Constant]) -> MDValue:
        return module.add_metadata(values)


class InlineAsm(ir.InlineAsm):
    @staticmethod
    def get(
        ftype: ir.FunctionType,
        asm: str,
        constraint: ir.Value,
        side_effect: bool = False,
    ) -> InlineAsm:
        return InlineAsm(ftype, asm, constraint, side_effect)
