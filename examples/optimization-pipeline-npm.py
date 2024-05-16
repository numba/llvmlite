try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

from ctypes import CFUNCTYPE, c_int, POINTER
import llvmlite.ir as ll
import llvmlite.binding as llvm


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

strmod = """
define i32 @foo3(i32* noalias nocapture readonly %src) {
entry:
  br label %loop.header

loop.header:
  %iv = phi i64 [ 0, %entry ], [ %inc, %loop.latch ]
  %r1  = phi i32 [ 0, %entry ], [ %r3, %loop.latch ]
  %arrayidx = getelementptr inbounds i32, i32* %src, i64 %iv
  %src_element = load i32, i32* %arrayidx, align 4
  %cmp = icmp eq i32 0, %src_element
  br i1 %cmp, label %loop.if, label %loop.latch

loop.if:
  %r2 = add i32 %r1, 1
  br label %loop.latch
loop.latch:
  %r3 = phi i32 [%r1, %loop.header], [%r2, %loop.if]
  %inc = add nuw nsw i64 %iv, 1
  %exitcond = icmp eq i64 %inc, 9
  br i1 %exitcond, label %loop.end, label %loop.header
loop.end:
  %r.lcssa = phi i32 [ %r3, %loop.latch ]
  ret i32 %r.lcssa
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
