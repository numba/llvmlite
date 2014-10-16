import llvmlite.ir as ll
import faulthandler; faulthandler.enable()


fnty = ll.FunctionType(ll.IntType(32), [ll.IntType(32).as_pointer(),
                                        ll.IntType(32)])
module = ll.Module()

func = ll.Function(module, fnty, name="sum")

bb_entry = func.append_basic_block()
bb_loop = func.append_basic_block()
bb_exit = func.append_basic_block()

builder = ll.IRBuilder()
builder.position_at_end(bb_entry)

builder.branch(bb_loop)
builder.position_at_end(bb_loop)

index = builder.phi(ll.IntType(32))
index.add_incoming(ll.Constant(index.type, 0), bb_entry)
accum = builder.phi(ll.IntType(32))
accum.add_incoming(ll.Constant(accum.type, 0), bb_entry)

ptr = builder.gep(func.args[0], [index])
value = builder.load(ptr)

added = builder.add(accum, value)
accum.add_incoming(added, bb_loop)

indexp1 = builder.add(index, ll.Constant(index.type, 1))
index.add_incoming(indexp1, bb_loop)

cond = builder.icmp_unsigned('<', indexp1, func.args[1])
builder.cbranch(cond, bb_loop, bb_exit)

builder.position_at_end(bb_exit)
builder.ret(added)

print(module)

import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, POINTER
import numpy as np


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

module.triple = llvm.get_default_triple()
llmod = llvm.parse_assembly(str(module))

# print(llmod)

with llvm.create_mcjit_compiler(llmod) as ee:

    # ee.add_module(llmod)
    ee.finalize_object()

    cfptr = ee.get_pointer_to_global(llmod.get_function('sum'))


    cfunc = CFUNCTYPE(c_int, POINTER(c_int), c_int)(cfptr)

    A = np.arange(10, dtype=np.int32)

    res = cfunc(A.ctypes.data_as(POINTER(c_int)), A.size)

    print(res, A.sum())

