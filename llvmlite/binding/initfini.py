from . import ffi


def initialize():
    ffi.lib.LLVMPY_InitializeCore()


def initialize_target():
    ffi.lib.LLVMPY_InitializeTarget()


def initialize_native_target():
    ffi.lib.LLVMPY_InitializeNativeTarget()


def initialize_all_target_infos():
    ffi.lib.LLVMPY_InitializeAllTargetInfos()


def initialize_all_targets():
    ffi.lib.LLVMPY_InitializeAllTargets()


def initialize_all_target_MCs():
    ffi.lib.LLVMPY_InitializeAllTargetMCs()


def shutdown():
    ffi.lib.LLVMPY_Shutdown()

