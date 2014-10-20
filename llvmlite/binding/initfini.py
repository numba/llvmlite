from . import ffi


def initialize():
    ffi.lib.LLVMPY_InitializeCore()


def initialize_native_target():
    ffi.lib.LLVMPY_InitializeNativeTarget()


def initialize_native_asmprinter():
    ffi.lib.LLVMPY_InitializeNativeAsmPrinter()


def shutdown():
    ffi.lib.LLVMPY_Shutdown()

