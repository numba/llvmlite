try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

from ctypes import CFUNCTYPE, c_int, POINTER
import llvmlite.ir as ll
import llvmlite.binding as llvm

import numpy as np

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

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

# Run -O3 optimization pipeline on the module

llmod = llvm.parse_assembly(strmod)
print(llmod)

target_machine = llvm.Target.from_default_triple().create_target_machine()

pto = llvm.create_pipeline_options()
pto.opt_level = 3
pb = llvm.create_pass_builder(target_machine, pto)
pm = pb.getNewModulePassManager()
pm.run(llmod, pb)

# pmb = llvm.create_pass_manager_builder()
# pmb.opt_level = 2
# pm = llvm.create_module_pass_manager()
# pmb.populate(pm)
# pm.run(llmod)

print(llmod)

with llvm.create_mcjit_compiler(llmod, target_machine) as ee:
    ee.finalize_object()
    cfptr = ee.get_function_address("sum")

    print("-- JIT compile:")

    print(target_machine.emit_assembly(llmod))

    cfunc = CFUNCTYPE(c_int, POINTER(c_int), c_int)(cfptr)
    A = np.arange(10, dtype=np.int32)
    res = cfunc(A.ctypes.data_as(POINTER(c_int)), A.size)

    print(res, A.sum())
