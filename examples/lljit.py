# Tutorial example from
# https://llvmlite.readthedocs.io/en/latest/user-guide/binding/examples.html
# adapted to use LLJIT instead of MCJIT
#
# Additionally this example also demonstrates that typed pointers still work in
# LLVM 14 (and 15, if built against that).

from ctypes import CFUNCTYPE, POINTER, c_double

import llvmlite.binding as llvm
import numpy as np

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

lljit = llvm.create_lljit_compiler()
rt = llvm.JITLibraryBuilder().add_ir(llvm_ir).export_symbol('fpadd')\
    .link(lljit, 'fpadd')

cfunc = CFUNCTYPE(c_double, c_double, c_double, POINTER(c_double))(rt['fpadd'])

# Create some floating point data and get a pointer to it that we can pass in
# to the jitted function
x = np.asarray([7.2])
data_ptr = x.ctypes.data_as(POINTER(c_double))


args = (1.0, 3.5, data_ptr)
res = cfunc(*args)
print(f"x[0] = {x[0]}")
print(f"fpadd({args[0]}, {args[1]}, &x[0]) = {res}")
