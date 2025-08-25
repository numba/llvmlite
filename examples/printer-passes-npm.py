# Demonstrates the printer and view passes in the new pass manager

try:
    import faulthandler; faulthandler.enable()
except ImportError:
    pass

import llvmlite.ir as ll
import llvmlite.binding as llvm


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

dbgmodstr = """
define void @f() !dbg !4 {
  ret void, !dbg !15
}

!llvm.dbg.cu = !{!0, !8}
!llvm.module.flags = !{!13, !16}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, producer: "clang version 3.4 (192092)", isOptimized: false, emissionKind: FullDebug, file: !1, enums: !2, retainedTypes: !2, globals: !2, imports: !2)
!1 = !DIFile(filename: "test1.c", directory: "/tmp")
!2 = !{}
!4 = distinct !DISubprogram(name: "f", line: 1, isLocal: false, isDefinition: true, virtualIndex: 6, isOptimized: false, unit: !0, scopeLine: 1, file: !1, scope: !5, type: !6, retainedNodes: !2)
!5 = !DIFile(filename: "test1.c", directory: "/tmp")
!6 = !DISubroutineType(types: !7)
!7 = !{null}
!8 = distinct !DICompileUnit(language: DW_LANG_C99, producer: "clang version 3.4 (192092)", isOptimized: false, emissionKind: FullDebug, file: !9, enums: !2, retainedTypes: !2, globals: !2, imports: !2)
!9 = !DIFile(filename: "test2.c", directory: "/tmp")
!11 = distinct !DISubprogram(name: "g", line: 1, isLocal: false, isDefinition: true, virtualIndex: 6, isOptimized: false, unit: !8, scopeLine: 1, file: !9, scope: !12, type: !6, retainedNodes: !2)
!12 = !DIFile(filename: "test2.c", directory: "/tmp")
!13 = !{i32 2, !"Dwarf Version", i32 4}
!14 = !DILocation(line: 1, scope: !4)
!15 = !DILocation(line: 1, scope: !11, inlinedAt: !14)
!16 = !{i32 1, !"Debug Info Version", i32 3}
"""


llmod = llvm.parse_assembly(strmod)
dbgmod = llvm.parse_assembly(dbgmodstr)

target_machine = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_tuning_options(speed_level=0)
pb = llvm.create_pass_builder(target_machine, pto)
pm = llvm.create_new_module_pass_manager()

pm.add_module_debug_info_pass()
pm.add_cfg_printer_pass()
pm.add_cfg_only_printer_pass()
pm.add_dom_printer_pass()
pm.add_dom_only_printer_pass()
pm.add_post_dom_printer_pass()
pm.add_post_dom_only_printer_pass()
pm.add_dom_only_printer_pass()
# Uncomment the following to launch viewers as required
# pm.add_post_dom_viewer_pass()
# pm.add_dom_viewer_pass()
# pm.add_post_dom_only_viewer_pass()

pm.run(llmod, pb)
pm.run(dbgmod, pb)
