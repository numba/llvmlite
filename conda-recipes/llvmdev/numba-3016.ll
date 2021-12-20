; Regression test for llvmdev-feedstock#52 and numba#3016

; Generated from C code: int a[1<<10],b[1<<10]; void foo() { int i=0; for(i=0; i<1<<10; i++) { b[i]=sin(a[i]); }}
; compiled: -fvectorize -fveclib=SVML -O -S -mavx -mllvm -disable-llvm-optzns -emit-llvm

; RUN: opt -vector-library=SVML -mcpu=haswell -O3 -S < %s | FileCheck %s
; CHECK: call {{.*}}__svml_sin4_ha(
; CHECK-NOT: call {{.*}}__svml_sin4(
; CHECK-NOT: call {{.*}}__svml_sin8

source_filename = "svml-3016.c"
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@a = common dso_local global [1024 x i32] zeroinitializer, align 16
@b = common dso_local global [1024 x i32] zeroinitializer, align 16

; Function Attrs: nounwind uwtable
define dso_local void @foo() #0 {
  %1 = alloca i32, align 4
  %2 = bitcast i32* %1 to i8*
  call void @llvm.lifetime.start.p0i8(i64 4, i8* %2) #3
  store i32 0, i32* %1, align 4, !tbaa !2
  store i32 0, i32* %1, align 4, !tbaa !2
  br label %3

; <label>:3:                                      ; preds = %17, %0
  %4 = load i32, i32* %1, align 4, !tbaa !2
  %5 = icmp slt i32 %4, 1024
  br i1 %5, label %6, label %20

; <label>:6:                                      ; preds = %3
  %7 = load i32, i32* %1, align 4, !tbaa !2
  %8 = sext i32 %7 to i64
  %9 = getelementptr inbounds [1024 x i32], [1024 x i32]* @a, i64 0, i64 %8
  %10 = load i32, i32* %9, align 4, !tbaa !2
  %11 = sitofp i32 %10 to double
  %12 = call double @"llvm.sin.f64"(double %11) #3
  %13 = fptosi double %12 to i32
  %14 = load i32, i32* %1, align 4, !tbaa !2
  %15 = sext i32 %14 to i64
  %16 = getelementptr inbounds [1024 x i32], [1024 x i32]* @b, i64 0, i64 %15
  store i32 %13, i32* %16, align 4, !tbaa !2
  br label %17

; <label>:17:                                     ; preds = %6
  %18 = load i32, i32* %1, align 4, !tbaa !2
  %19 = add nsw i32 %18, 1
  store i32 %19, i32* %1, align 4, !tbaa !2
  br label %3

; <label>:20:                                     ; preds = %3
  %21 = bitcast i32* %1 to i8*
  call void @llvm.lifetime.end.p0i8(i64 4, i8* %21) #3
  ret void
}

; Function Attrs: argmemonly nounwind
declare void @llvm.lifetime.start.p0i8(i64, i8* nocapture) #1

; Function Attrs: nounwind
declare dso_local double @"llvm.sin.f64"(double) #2

; Function Attrs: argmemonly nounwind
declare void @llvm.lifetime.end.p0i8(i64, i8* nocapture) #1

attributes #0 = { nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+avx,+fxsr,+mmx,+popcnt,+sse,+sse2,+sse3,+sse4.1,+sse4.2,+ssse3,+x87,+xsave" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { argmemonly nounwind }
attributes #2 = { nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+avx,+fxsr,+mmx,+popcnt,+sse,+sse2,+sse3,+sse4.1,+sse4.2,+ssse3,+x87,+xsave" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #3 = { nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 7.0.0- (trunk)"}
!2 = !{!3, !3, i64 0}
!3 = !{!"int", !4, i64 0}
!4 = !{!"omnipotent char", !5, i64 0}
!5 = !{!"Simple C/C++ TBAA"}
