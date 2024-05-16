try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

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

# Run loop-unroll + simplifycfg on module

llmod = llvm.parse_assembly(strmod)
print(llmod)

target_machine = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_options()
pto.opt_level = 0
pb = llvm.create_pass_builder(target_machine, pto)

pm = llvm.create_new_module_pass_manager()
pm.add_loop_unroll_pass()
pm.add_simplify_cfg_pass()
pm.run(llmod, pb)

print(llmod)
