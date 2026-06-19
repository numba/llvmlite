; From LLVM upstream commit c327ab359a959de2e4241a5fcda409958f2c0d11 (PR #204347):
; https://github.com/llvm/llvm-project/commit/c327ab359a959de2e4241a5fcda409958f2c0d11
; llvmdev is built with assertions,
; so the recipe runs the built llc on this and the unpatched backend aborts.

; This test uses a Windows triple with ELF binaries. This triple does not use
; Windows CFI. Since it's Windows though it uses the
; CSR_Win_AArch64_AAPCS_SaveList for callee-saves.
;
; Functions with a large stack reserve and extra register, so this function will
; save x28 followed by the frame record. This test checks we do not attempt to
; pair x28 with the frame pointer (x29). Previously we would, as we'd not
; recognize aarch64-pc-windows-msvc-elf as Windows in FrameLowering and
; handle it as if it was using the default CSR_AArch64_AAPCS_SaveList, and fail
; to invalidate the pairing.

target triple = "aarch64-pc-windows-msvc-elf"

define i32 @large_stack_requires_frame_record() "frame-pointer"="all" nounwind {
  %x = alloca [500 x i8], align 16
  call void @baz(ptr %x)
  ret i32 0
}

declare void @baz(ptr)
