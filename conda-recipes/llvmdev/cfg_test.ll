; ModuleID = 'foo'
source_filename = "<string>"
target datalayout = "e-m:o-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-apple-darwin17.4.0"

@.const.foo = internal constant [4 x i8] c"foo\00"
@".const.Fatal error: missing _dynfunc.Closure" = internal constant [38 x i8] c"Fatal error: missing _dynfunc.Closure\00"
@PyExc_RuntimeError = external global i8
@".const.missing Environment" = internal constant [20 x i8] c"missing Environment\00"

; Function Attrs: norecurse nounwind
declare i32 @"_ZN8__main__7foo$241Ex"(i64* noalias nocapture %retptr, { i8*, i32 }** noalias nocapture readnone %excinfo, i8* noalias nocapture readnone %env, i64 %arg.x) local_unnamed_addr #0


define i8* @"testme"(i8* %py_closure, i8* %py_args, i8* nocapture readnone %py_kws) local_unnamed_addr {
entry:
  %.5 = alloca i8*, align 8
  %.6 = call i32 (i8*, i8*, i64, i64, ...) @PyArg_UnpackTuple(i8* %py_args, i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.const.foo, i64 0, i64 0), i64 1, i64 1, i8** nonnull %.5)
  %.7 = icmp eq i32 %.6, 0
  br i1 %.7, label %entry_if, label %entry_endif, !prof !0

entry_if:                                         ; preds = %entry.endif.1.1.endif, %entry
  ret i8* null

entry_endif:                                      ; preds = %entry
  %.11 = icmp eq i8* %py_closure, null
  ret i8* null

}

declare i32 @PyArg_UnpackTuple(i8*, i8*, i64, i64, ...) local_unnamed_addr

; Function Attrs: nounwind
declare i32 @puts(i8* nocapture readonly) local_unnamed_addr #1

declare void @PyErr_SetString(i8*, i8*) local_unnamed_addr

declare i8* @PyNumber_Long(i8*) local_unnamed_addr

declare i64 @PyLong_AsLongLong(i8*) local_unnamed_addr

declare void @Py_DecRef(i8*) local_unnamed_addr

declare i8* @PyErr_Occurred() local_unnamed_addr

declare i8* @PyLong_FromLongLong(i64) local_unnamed_addr

; Function Attrs: nounwind
declare void @llvm.stackprotector(i8*, i8**) #1

attributes #0 = { norecurse nounwind }
attributes #1 = { nounwind }

!0 = !{!"branch_weights", i32 1, i32 9}
!1 = !{!"branch_weights", i32 9, i32 1}

