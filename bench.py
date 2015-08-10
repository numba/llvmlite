"""
Crude benchmark to compare llvmlite and llvmpy performance.
"""

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


def run_bench(verbose):
    t = time()

    int32 = lc.Type.int(32)
    fnty = lc.Type.function(int32, [lc.Type.pointer(int32), int32])
    module = lc.Module.new('foo')

    func = lc.Function.new(module, fnty, name="sum")

    bb_entry = func.append_basic_block('entry')
    bb_loop = func.append_basic_block('loop')
    bb_exit = func.append_basic_block('exit')

    builder = lc.Builder.new(bb_entry)
    builder.position_at_end(bb_entry)

    builder.branch(bb_loop)
    builder.position_at_end(bb_loop)

    index = builder.phi(int32)
    index.add_incoming(lc.Constant.int(index.type, 0), bb_entry)
    accum = builder.phi(int32)
    accum.add_incoming(lc.Constant.int(accum.type, 0), bb_entry)

    ptr = builder.gep(func.args[0], [index])
    value = builder.load(ptr)

    added = builder.add(accum, value)
    accum.add_incoming(added, bb_loop)

    indexp1 = builder.add(index, lc.Constant.int(index.type, 1))
    index.add_incoming(indexp1, bb_loop)

    cond = builder.icmp(lc.ICMP_ULT, indexp1, func.args[1])
    builder.cbranch(cond, bb_loop, bb_exit)

    builder.position_at_end(bb_exit)
    builder.ret(added)

    #strmod = str(module)

    dt = time() - t
    if verbose:
        print("generate IR: %s" % (dt,))

    t = time()

    eb = ee.EngineBuilder.new(module) #.opt(3)
    tm = ee.TargetMachine.new(opt=2)
    engine = eb.create(tm)

    dt = time() - t
    if verbose:
        print("create EngineBuilder: %s" % (dt,))

    t = time()

    if hasattr(eb, "module"):
        # llvmlite
        llmod = eb.module
        llfunc = llmod.get_function("sum")
    else:
        llmod = module
        llfunc = llmod.get_function_named("sum")

    cfptr = engine.get_pointer_to_function(llfunc)

    dt = time() - t
    if verbose:
        print("JIT compile: %s" % (dt,))

    # Check function calling
    cfunc = CFUNCTYPE(c_int, POINTER(c_int), c_int)(cfptr)
    A = np.arange(10, dtype=np.int32)
    res = cfunc(A.ctypes.data_as(POINTER(c_int)), A.size)

    assert res == A.sum(), (res, A.sum())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s (llvmlite|llvmpy)"
              % (sys.executable,), file=sys.stderr)
        sys.exit(1)
    impl = sys.argv[1]

    if impl == 'llvmlite':
        import llvmlite.binding as llvm
        import llvmlite.llvmpy.core as lc
        from llvmlite.llvmpy import ee

        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        del llvm

    elif impl == 'llvmpy':
        import llvm.core as lc
        from llvm import ee

    else:
        raise RuntimeError("Wrong implementation %r" % (impl,))

    for i in range(3):
        run_bench(True)
        print()
