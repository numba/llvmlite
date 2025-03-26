"""
This example demonstrates how to optimize a module with a module pass manager
pre-populated with passes according to a given optimization level.

The optimized module is executed using the MCJIT bindings.
"""

from ctypes import CFUNCTYPE, c_int, POINTER
import faulthandler
import llvmlite.binding as llvm

import numpy as np

# Dump Python traceback in the event of a segfault
faulthandler.enable()

# All are required to initialize LLVM
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Module to optimize and execute
strmod = """
; ModuleID = '<string>'
source_filename = "<string>"
target triple = "unknown-unknown-unknown"

define i32 @sum(i32* %.1, i32 %.2) {
.4:
  br label %.5

.5:                                               ; preds = %.5, %.4
  %.8 = phi i32 [ 0, %.4 ], [ %.13, %.5 ]
  %.9 = phi i32 [ 0, %.4 ], [ %.12, %.5 ]
  %.10 = getelementptr i32, i32* %.1, i32 %.8
  %.11 = load i32, i32* %.10, align 4
  %.12 = add i32 %.9, %.11
  %.13 = add i32 %.8, 1
  %.14 = icmp ult i32 %.13, %.2
  br i1 %.14, label %.5, label %.6

.6:                                               ; preds = %.5
  ret i32 %.12
}
"""


module = llvm.parse_assembly(strmod)

print("Module before optimization:\n")
print(module)

# Create a ModulePassManager for speed optimization level 3
target_machine = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_tuning_options(speed_level=3)
pb = llvm.create_pass_builder(target_machine, pto)
pm = pb.getModulePassManager()

# Run the optimization pipeline on the module
pm.run(module, pb)

# O3 optimization will likely have vectorized the loop. The resulting code will
# be more complex, but more performant.
print("\nModule after optimization:\n")
print(module)

with llvm.create_mcjit_compiler(module, target_machine) as ee:
    # Generate code and get a pointer to it for calling
    ee.finalize_object()
    cfptr = ee.get_function_address("sum")

    # We should also observe vector instructions in the generated assembly
    print("\nAssembly code generated from module\n")
    print(target_machine.emit_assembly(module))

    # Create an array of integers and call our optimized sum function with them
    cfunc = CFUNCTYPE(c_int, POINTER(c_int), c_int)(cfptr)
    A = np.arange(10, dtype=np.int32)
    res = cfunc(A.ctypes.data_as(POINTER(c_int)), A.size)

    # Print results, which should be identical
    print(f"Result of executing the optimized function: {res}")
    print(f"Expected result: {A.sum()}")

    # Sanity check
    np.testing.assert_equal(res, A.sum())
    print("Success!")
