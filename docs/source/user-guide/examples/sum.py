from __future__ import print_function

from ctypes import CFUNCTYPE, c_int, POINTER
import sys
try:
    from time import perf_counter as time
except ImportError:
    from time import time

import numpy as np

try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

import llvmlite.ir as ll
import llvmlite.binding as llvm


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


t1 = time()

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

strmod = str(module)

t2 = time()

print("-- generate IR:", t2-t1)

t3 = time()

llmod = llvm.parse_assembly(strmod)

t4 = time()

print("-- parse assembly:", t4-t3)

print(llmod)

pmb = llvm.create_pass_manager_builder()
pmb.opt_level = 2
pm = llvm.create_module_pass_manager()
pmb.populate(pm)

t5 = time()

pm.run(llmod)

t6 = time()

print("-- optimize:", t6-t5)

t7 = time()

target_machine = llvm.Target.from_default_triple().create_target_machine()

with llvm.create_mcjit_compiler(llmod, target_machine) as ee:
    ee.finalize_object()
    cfptr = ee.get_function_address("sum")

    t8 = time()
    print("-- JIT compile:", t8 - t7)

    print(target_machine.emit_assembly(llmod))

    cfunc = CFUNCTYPE(c_int, POINTER(c_int), c_int)(cfptr)
    A = np.arange(10, dtype=np.int32)
    res = cfunc(A.ctypes.data_as(POINTER(c_int)), A.size)

    print(res, A.sum())

