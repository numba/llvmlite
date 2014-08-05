define i32 @foo(i32 %.0, i32 %.1) noreturn
{
.2:
%.3 = alloca i32
store i32 123, i32* %.3
%.5 = load i32* %.3
%.6 = add i32 %.0, %.1
%.7 = mul i32 %.6, 123
%.8 = icmp slt i32 %.6, %.7
ret i32 %.7
.10:
%.12 = trunc i32 %.6 to i1
br i1 %.12, label %.10, label %.11
.11:
ret i32 %.5
}

