from __future__ import annotations

from ctypes import c_uint

from llvmlite.binding import ffi


def initialize() -> None:
    """
    Initialize the LLVM core.
    """
    ffi.lib.LLVMPY_InitializeCore()


def initialize_all_targets() -> None:
    """
    Initialize all targets. Necessary before targets can be looked up
    via the :class:`Target` class.
    """
    ffi.lib.LLVMPY_InitializeAllTargetInfos()
    ffi.lib.LLVMPY_InitializeAllTargets()
    ffi.lib.LLVMPY_InitializeAllTargetMCs()


def initialize_all_asmprinters() -> None:
    """
    Initialize all code generators. Necessary before generating
    any assembly or machine code via the :meth:`TargetMachine.emit_object`
    and :meth:`TargetMachine.emit_assembly` methods.
    """
    ffi.lib.LLVMPY_InitializeAllAsmPrinters()


def initialize_native_target() -> None:
    """
    Initialize the native (host) target.  Necessary before doing any
    code generation.
    """
    ffi.lib.LLVMPY_InitializeNativeTarget()


def initialize_native_asmprinter() -> None:
    """
    Initialize the native ASM printer.
    """
    ffi.lib.LLVMPY_InitializeNativeAsmPrinter()


def initialize_native_asmparser() -> None:
    """
    Initialize the native ASM parser.
    """
    ffi.lib.LLVMPY_InitializeNativeAsmParser()


def shutdown() -> None:
    ffi.lib.LLVMPY_Shutdown()


# =============================================================================
# Set function FFI

ffi.lib.LLVMPY_GetVersionInfo.restype = c_uint


def _version_info() -> tuple[int, ...]:
    v: list[int] = []
    x = ffi.lib.LLVMPY_GetVersionInfo()
    while x:
        v.append(x & 0xFF)
        x >>= 8
    return tuple(reversed(v))


llvm_version_info = _version_info()
