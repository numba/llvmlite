from __future__ import print_function

from ctypes import CFUNCTYPE, c_int, POINTER

try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

import llvmlite.binding as llvm


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

ir_4_fold = r"""
; ModuleID = "examples/ir_fpadd.py"
target triple = "unknown-unknown-unknown"

declare void @foo()

define void @test4_fold(i32 %a, i32 %b) {
  %cmp1 = icmp eq i32 %a, %b
  br i1 %cmp1, label %taken, label %untaken

taken:
  %cmp2 = icmp ugt i32 %a, 0
  br i1 %cmp2, label %else, label %untaken

else:
  call void @foo()
  ret void

untaken:
  ret void
}
"""

ir_multiple_passes = r"""
define i32 @foo() {
entry:
  br label %for.foo.cond

for.foo.cond:                                         ; preds = %entry
  br i1 false, label %for.foo.body, label %for.foo.end3

for.foo.body:                                         ; preds = %for.foo.cond
  br label %for.foo.cond1

for.foo.cond1:                                        ; preds = %for.foo.body
  br i1 false, label %for.foo.body2, label %for.foo.end

for.foo.body2:                                        ; preds = %for.foo.cond1
  unreachable

for.foo.end:                                          ; preds = %for.foo.cond1
  unreachable

for.foo.end3:                                         ; preds = %for.foo.cond
  ret i32 undef
}
"""

ir_default = r"""
define i32 @foo(i32 %i) {
    %r = add i32 1, 1
    ret i32 %r
}
"""

target_machine = llvm.Target.from_default_triple().create_target_machine()
npm = llvm.create_pass_builder_options()


# Run single pass with new pass manager
mod = llvm.parse_assembly(ir_4_fold)
mod.verify()
error = npm.runPasses(mod, target_machine, "simplifycfg")

# Run multiple passes by passing them as string
mod2 = llvm.parse_assembly(ir_multiple_passes)
mod2.verify()
error = npm.runPasses(mod2, target_machine, "break-crit-edges,lowerswitch,mergereturn")


# Run default O0 optimization pipeline
mod3 = llvm.parse_assembly(ir_default)
mod3.verify()
error = npm.runPasses(mod3, target_machine, "default<O0>")


# Run default O3 optimization pipeline
mod4 = llvm.parse_assembly(ir_default)
mod4.verify()
error = npm.runPasses(mod4, target_machine, "default<O3>")
