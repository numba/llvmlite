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

