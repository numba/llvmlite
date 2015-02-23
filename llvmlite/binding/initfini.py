from ctypes import c_uint

from . import ffi


def initialize():
    """
    Initialize the LLVM core.
    """
    ffi.lib.LLVMPY_InitializeCore()


def initialize_native_target():
    """
    Initialize the native (host) target.  Necessary before doing any
    code generation.
    """
    ffi.lib.LLVMPY_InitializeNativeTarget()


def initialize_native_asmprinter():
    """
    Initialize the native ASM printer.
    """
    ffi.lib.LLVMPY_InitializeNativeAsmPrinter()


def shutdown():
    ffi.lib.LLVMPY_Shutdown()


# =============================================================================
# Set function FFI

ffi.lib.LLVMPY_GetVersionInfo.restype = c_uint


def _version_info():
    v = []
    x = ffi.lib.LLVMPY_GetVersionInfo()
    while x:
        v.append(x & 0xff)
        x >>= 8
    return tuple(reversed(v))

llvm_version_info = _version_info()
