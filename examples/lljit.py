# Tutorial example from
# https://llvmlite.readthedocs.io/en/latest/user-guide/binding/examples.html
# adapted to use LLJIT instead of MCJIT
#
# Additionally this example also demonstrates that typed pointers still work in
# LLVM 14 (and 15, if built against that).

from ctypes import CFUNCTYPE, c_double, c_int, c_uint64

import llvmlite.binding as llvm
import numpy as np

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()  # yes, even this one

llvm_ir = """
   ; ModuleID = "examples/ir_fpadd.py"
   target triple = "unknown-unknown-unknown"
   target datalayout = ""

   define double @"fpadd"(double %".1", double %".2", double* %"dummy")
   {
   entry:
     %"res" = fadd double %".1", %".2"
     %"val" = load double, double* %"dummy"
     %"res2" = fadd double %"res", %"val"
     ret double %"res2"
   }
   """

mod = llvm.parse_assembly(llvm_ir)
mod.verify()

lljit = llvm.create_lljit_compiler()
lljit.add_ir_module(mod)

func_ptr = lljit.lookup('fpadd')
cfunc = CFUNCTYPE(c_double, c_double, c_double, c_uint64)(func_ptr)

# Create some floating point data and get a pointer to it that we can pass in
# to the jitted function
x = np.asarray([7.2])
data_ptr = x.__array_interface__['data'][0]


args = (1.0, 3.5, data_ptr)
res = cfunc(*args)
print(f"x[0] = {x[0]}")
print(f"fpadd({args[0]}, {args[1]}, &x[0]) = {res}")
