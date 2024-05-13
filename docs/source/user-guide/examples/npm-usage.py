try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

import llvmlite.ir as ll
import llvmlite.binding as llvm


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


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
added = builder.add(accum, ll.Constant(index.type, 0))
accum.add_incoming(added, bb_loop)
indexp1 = builder.add(index, ll.Constant(index.type, 1))
index.add_incoming(indexp1, bb_loop)
cond = builder.icmp_unsigned('<', indexp1, func.args[1])
builder.cbranch(cond, bb_loop, bb_exit)
builder.position_at_end(bb_exit)
builder.ret(added)
strmod = str(module)

strmod2 = """
; RUN: opt -simplifycfg -S --preserve-ll-uselistorder %s | FileCheck %s
; REQUIRES: x86-registered-target
; CHECK-LABEL: @n
; CHECK: uselistorder i16 0, { 3, 2, 4, 1, 5, 0, 6 }
; Note: test was added in an effort to ensure determinism when updating memoryssa. See PR42574.
; If the uselistorder check becomes no longer relevant, the test can be disabled or removed.
%rec9 = type { i16, i32, i32 }
@a = global [1 x [1 x %rec9]] zeroinitializer
define i16 @n() {
  br label %..split_crit_edge
..split_crit_edge:                                ; preds = %0
  br label %.split
bb4.us4:                                          ; preds = %bb2.split.us32, %bb6.us28
  %i.4.01.us5 = phi i16 [ %_tmp49.us30, %bb6.us28 ]
  br label %g.exit4.us21
bb1.i.us14:                                       ; preds = %bb4.us4
  br label %g.exit4.us21
g.exit4.us21:                                     ; preds = %bb1.i.us14, %g.exit4.critedge.us9
  %i.4.02.us22 = phi i16 [ %i.4.01.us5, %bb4.us4 ], [ %i.4.01.us5, %bb1.i.us14 ]
  br label %bb6.us28
bb5.us26:                                         ; preds = %g.exit4.us21
  br label %bb6.us28
bb6.us28:                                         ; preds = %bb5.us26, %g.exit4.us21
  %i.4.03.us29 = phi i16 [ %i.4.02.us22, %bb5.us26 ], [ %i.4.02.us22, %g.exit4.us21 ]
  %_tmp49.us30 = add nuw nsw i16 %i.4.03.us29, 1
  br label %bb4.us4
bb4.us.us:                                        ; preds = %bb2.split.us.us, %bb6.us.us
  %i.4.01.us.us = phi i16  [ %_tmp49.us.us, %bb6.us.us ]
  br label %bb1.i.us.us
bb1.i.us.us:                                      ; preds = %bb4.us.us
  br label %g.exit4.us.us
g.exit4.us.us:                                    ; preds = %bb1.i.us.us, %g.exit4.critedge.us.us
  %i.4.02.us.us = phi i16 [ %i.4.01.us.us, %bb1.i.us.us ]
  br label %bb5.us.us
bb5.us.us:                                        ; preds = %g.exit4.us.us
  br label %bb6.us.us
bb6.us.us:                                        ; preds = %bb5.us.us, %g.exit4.us.us
  %i.4.03.us.us = phi i16 [ %i.4.02.us.us, %bb5.us.us ]
  %_tmp49.us.us = add nuw nsw i16 %i.4.03.us.us, 1
  br label %bb4.us.us
.split:                                           ; preds = %..split_crit_edge
  br label %bb2
bb2:                                              ; preds = %.split, %bb7
  %h.3.0 = phi i16 [ undef, %.split ], [ %_tmp53, %bb7 ]
  br label %bb2.bb2.split_crit_edge
bb2.bb2.split_crit_edge:                          ; preds = %bb2
  br label %bb2.split
bb2.split.us:                                     ; preds = %bb2
  br label %bb4.us
bb4.us:                                           ; preds = %bb6.us, %bb2.split.us
  %i.4.01.us = phi i16 [ 0, %bb2.split.us ]
  br label %bb1.i.us
g.exit4.critedge.us:                              ; preds = %bb4.us
  br label %g.exit4.us
bb1.i.us:                                         ; preds = %bb4.us
  br label %g.exit4.us
g.exit4.us:                                       ; preds = %bb1.i.us, %g.exit4.critedge.us
  %i.4.02.us = phi i16 [ %i.4.01.us, %g.exit4.critedge.us ], [ %i.4.01.us, %bb1.i.us ]
  br label %bb5.us
bb5.us:                                           ; preds = %g.exit4.us
  br label %bb7
bb2.split:                                        ; preds = %bb2.bb2.split_crit_edge
  br label %bb4

bb4:                                              ; preds = %bb2.split, %bb6
  %i.4.01 = phi i16 [ 0, %bb2.split ]
  %_tmp16 = getelementptr [1 x [1 x %rec9]], [1 x [1 x %rec9]]* @a, i16 0, i16 %h.3.0, i16 %i.4.01, i32 0
  %_tmp17 = load i16, i16* %_tmp16, align 1
  br label %g.exit4.critedge

bb1.i:                                            ; preds = %bb4
  br label %g.exit4

g.exit4.critedge:                                 ; preds = %bb4
  %_tmp28.c = getelementptr [1 x [1 x %rec9]], [1 x [1 x %rec9]]* @a, i16 0, i16 %h.3.0, i16 %i.4.01, i32 1
  %_tmp29.c = load i32, i32* %_tmp28.c, align 1
  %_tmp30.c = trunc i32 %_tmp29.c to i16
  br label %g.exit4

g.exit4:                                          ; preds = %g.exit4.critedge, %bb1.i
  %i.4.02 = phi i16 [ %i.4.01, %g.exit4.critedge ], [ %i.4.01, %bb1.i ]
  %_tmp41 = getelementptr [1 x [1 x %rec9]], [1 x [1 x %rec9]]* @a, i16 0, i16 %h.3.0, i16 %i.4.02, i32 2
  br label %bb6

bb5:                                              ; preds = %g.exit4
  br label %bb6
bb6:                                              ; preds = %bb5, %g.exit4
  %i.4.03 = phi i16 [ %i.4.02, %bb5 ], [ %i.4.02, %g.exit4 ]
  %_tmp49 = add nuw nsw i16 %i.4.03, 1
  br label %bb7
bb7:                                              ; preds = %bb7.us-lcssa.us, %bb7.us-lcssa
  %_tmp53 = add nsw i16 %h.3.0, 1
  br label %bb2
}
"""

strunroll = """
define dso_local i32 @test(i64 %a, i64 %b, i64 %c) local_unnamed_addr {
entry:
  br label %for.body

for.cond.cleanup:                                 ; preds = %for.body
  %cmp6 = icmp eq i32 %val.2, 0
  %cond = zext i1 %cmp6 to i32
  ret i32 %cond

for.body:                                         ; preds = %for.body, %entry
  %i.018 = phi i64 [ 0, %entry ], [ %inc, %for.body ]
  %val.017 = phi i32 [ 0, %entry ], [ %val.2, %for.body ]
  %a.addr.016 = phi i64 [ %a, %entry ], [ %add, %for.body ]
  %b.addr.015 = phi i64 [ %b, %entry ], [ %add5, %for.body ]
  %cmp1 = icmp ugt i64 %a.addr.016, %b.addr.015
  %add = add i64 %a.addr.016, %b.addr.015
  %cmp2 = icmp ugt i64 %b.addr.015, %c
  %0 = or i1 %cmp2, %cmp1
  %val.2 = select i1 %0, i32 1, i32 %val.017
  %add5 = add i64 %b.addr.015, %c
  %inc = add nuw nsw i64 %i.018, 1
  %exitcond = icmp eq i64 %inc, 100
  br i1 %exitcond, label %for.cond.cleanup, label %for.body, !llvm.loop !2
}
; CHECK: [[VAL:r[0-9]+]] = w{{[0-9]+}}
; CHECK-NOT: [[VAL:r[0-9]+]] <<= 32
; CHECK-NOT: [[VAL]] >>= 32
; CHECK: if [[VAL]] == 0 goto

!2 = distinct !{!2, !3}
!3 = !{!"llvm.loop.unroll.enable"}
"""

strunroll2 = """
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

# check default pipeline + simplifycfg on module
npm2 = llvm.create_new_module_pass_manager()
llmod = llvm.parse_assembly(strmod)
print(llmod)
tm = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_options()
pto.opt_level = 2    # similarly more properties can be set
pb = llvm.create_pass_builder(tm, pto)
npm_o2 = pb.getModulePassManager()
npm_o2.run(llmod, pb)
print(llmod)


# npm.add_simplify_cfg_pass()
# npm.run(llmod2, pb)
# print("Simplified module 2 *******")
# print(llmod2)


# check default pipeline + simplifycfg on a function
llmod2 = llvm.parse_assembly(strmod2)
tm = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_options()
pto.opt_level = 3    # similarly more properties can be set
pb = llvm.create_pass_builder(tm, pto)
fun = llmod2.get_function("n")
print(fun)
fpm = pb.getFunctionPassManager()
fpm.add_simplify_cfg_pass()
fpm.run(fun, pb)
print(fun)


# Check loop_unrolling option in PTO
llmod_unroll = llvm.parse_assembly(strunroll2)
print(llmod_unroll)
tm = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_options()
pto.opt_level = 3    # similarly more properties can be set
pto.loop_unrolling = False
pb = llvm.create_pass_builder(tm, pto)
npm = pb.getModulePassManager()
# # Inplace optimize the IR module
npm.run(llmod_unroll, pb)
print(llmod_unroll)


# Check loop rotate
npm2 = llvm.create_new_module_pass_manager()
npm2.add_loop_rotate_pass()
npm2.run(llmod_unroll, pb)
print(llmod_unroll)


# Check instcombine
npm3 = llvm.create_new_module_pass_manager()
npm3.add_instruction_combine_pass()
npm3.run(llmod_unroll, pb)
print(llmod_unroll)
