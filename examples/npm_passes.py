"""
This example demonstrates how to use the new module pass manager to optimize a
module using the loop unrolling and CFG simplification passes.
"""

import faulthandler
import llvmlite.binding as llvm

# Dump Python traceback in the event of a segfault
faulthandler.enable()

# All are required to initialize LLVM
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Module to optimize
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


module = llvm.parse_assembly(strmod)

print("Module before optimization:\n")
print(module)

# Set up the module pass manager used to run our optimization pipeline.
# We create it unpopulated, and then add the loop unroll and simplify CFG
# passes.
pm = llvm.create_new_module_pass_manager()
pm.add_loop_unroll_pass()
pm.add_simplify_cfg_pass()


# To run the pass manager, we need a pass builder object - we create pipeline
# tuning options with no optimization, then use that to create a pass builder.
target_machine = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_tuning_options(speed_level=0)
pb = llvm.create_pass_builder(target_machine, pto)

# Now we can run the pass manager on our module
pm.run(module, pb)


# We should observer a fully unrolled loop, and the function now consists of a
# single basic block executing all the iterations of the loop in a straight
# line.
print("\nModule after optimization:\n")
print(module)
