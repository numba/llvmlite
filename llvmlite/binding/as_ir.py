from functools import singledispatch

from llvmlite.ir.context import global_context


def as_ir(llvm_value):
    return as_ir_context(llvm_value, context=global_context)


@singledispatch
def as_ir_context(llvm_value, context):
    raise NotImplementedError(type(llvm_value))


