from ctypes import c_bool, c_int, c_size_t, c_char_p, POINTER
from enum import IntFlag
from llvmlite.binding import ffi


def create_new_module_pass_manager():
    return ModulePassManager()


def create_new_function_pass_manager():
    return FunctionPassManager()


def create_pass_builder(tm, pto):
    return PassBuilder(tm, pto)


def create_pipeline_tuning_options(speed_level=2, size_level=0):
    return PipelineTuningOptions(speed_level, size_level)


class RefPruneSubpasses(IntFlag):
    PER_BB       = 0b0001    # noqa: E221
    DIAMOND      = 0b0010    # noqa: E221
    FANOUT       = 0b0100    # noqa: E221
    FANOUT_RAISE = 0b1000
    ALL = PER_BB | DIAMOND | FANOUT | FANOUT_RAISE


class ModulePassManager(ffi.ObjectRef):

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_CreateNewModulePassManager()
        super().__init__(ptr)

    def run(self, module, pb):
        ffi.lib.LLVMPY_RunNewModulePassManager(self, module, pb)

    def add_verifier(self):
        ffi.lib.LLVMPY_AddVerifierPass(self)

    def add_aa_eval_pass(self):
        ffi.lib.LLVMPY_AddAAEvalPass_module(self)

    def add_simplify_cfg_pass(self):
        ffi.lib.LLVMPY_AddSimplifyCFGPass_module(self)

    def add_loop_unroll_pass(self):
        ffi.lib.LLVMPY_AddLoopUnrollPass_module(self)

    def add_loop_rotate_pass(self):
        ffi.lib.LLVMPY_AddLoopRotatePass_module(self)

    def add_instruction_combine_pass(self):
        ffi.lib.LLVMPY_AddInstructionCombinePass_module(self)

    def add_jump_threading_pass(self, threshold=-1):
        ffi.lib.LLVMPY_AddJumpThreadingPass_module(self, threshold)

    def _dispose(self):
        ffi.lib.LLVMPY_DisposeNewModulePassManger(self)

    # Non-standard LLVM passes
    def add_refprune_pass(self, subpasses_flags=RefPruneSubpasses.ALL,
                          subgraph_limit=1000):
        """Add Numba specific Reference count pruning pass.

        Parameters
        ----------
        subpasses_flags : RefPruneSubpasses
            A bitmask to control the subpasses to be enabled.
        subgraph_limit : int
            Limit the fanout pruners to working on a subgraph no bigger than
            this number of basic-blocks to avoid spending too much time in very
            large graphs. Default is 1000. Subject to change in future
            versions.
        """
        iflags = RefPruneSubpasses(subpasses_flags)
        ffi.lib.LLVMPY_AddRefPrunePass_module(self, iflags, subgraph_limit)


class FunctionPassManager(ffi.ObjectRef):

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_CreateNewFunctionPassManager()
        super().__init__(ptr)

    def run(self, fun, pb):
        ffi.lib.LLVMPY_RunNewFunctionPassManager(self, fun, pb)

    def add_aa_eval_pass(self):
        ffi.lib.LLVMPY_AddAAEvalPass_function(self)

    def add_simplify_cfg_pass(self):
        ffi.lib.LLVMPY_AddSimplifyCFGPass_function(self)

    def add_loop_unroll_pass(self):
        ffi.lib.LLVMPY_AddLoopUnrollPass_function(self)

    def add_loop_rotate_pass(self):
        ffi.lib.LLVMPY_AddLoopRotatePass_function(self)

    def add_instruction_combine_pass(self):
        ffi.lib.LLVMPY_AddInstructionCombinePass_function(self)

    def add_jump_threading_pass(self, threshold=-1):
        ffi.lib.LLVMPY_AddJumpThreadingPass_function(self, threshold)

    def _dispose(self):
        ffi.lib.LLVMPY_DisposeNewFunctionPassManger(self)

    # Non-standard LLVM passes
    def add_refprune_pass(self, subpasses_flags=RefPruneSubpasses.ALL,
                          subgraph_limit=1000):
        """Add Numba specific Reference count pruning pass.

        Parameters
        ----------
        subpasses_flags : RefPruneSubpasses
            A bitmask to control the subpasses to be enabled.
        subgraph_limit : int
            Limit the fanout pruners to working on a subgraph no bigger than
            this number of basic-blocks to avoid spending too much time in very
            large graphs. Default is 1000. Subject to change in future
            versions.
        """
        iflags = RefPruneSubpasses(subpasses_flags)
        ffi.lib.LLVMPY_AddRefPrunePass_function(self, iflags, subgraph_limit)


class PipelineTuningOptions(ffi.ObjectRef):

    def __init__(self, speed_level=2, size_level=0):
        self._speed_level = None
        self._size_level = None
        self.speed_level = speed_level
        self.size_level = size_level
        super().__init__(ffi.lib.LLVMPY_CreatePipelineTuningOptions())

    @property
    def speed_level(self):
        return self._speed_level

    @speed_level.setter
    def speed_level(self, value):
        if not 0 <= value <= 3:
            raise ValueError(
                "Optimization level for speed should be 0, 1, 2, or 3")
        self._speed_level = value

    @property
    def size_level(self):
        return self._size_level

    @size_level.setter
    def size_level(self, value):
        if not 0 <= value <= 2:
            raise ValueError("Optimization level for size should be 0, 1, or 2")
        if value != 0 and self.speed_level != 2:
            raise ValueError(
                "Optimization for size should be encoded with speed level == 2")
        self._size_level = value

    @property
    def loop_interleaving(self):
        return ffi.lib.LLVMPY_PTOGetLoopInterleaving(self)

    @loop_interleaving.setter
    def loop_interleaving(self, value):
        ffi.lib.LLVMPY_PTOSetLoopInterleaving(self, value)

    @property
    def loop_vectorization(self):
        return ffi.lib.LLVMPY_PTOGetLoopVectorization(self)

    @loop_vectorization.setter
    def loop_vectorization(self, value):
        ffi.lib.LLVMPY_PTOSetLoopVectorization(self, value)

    @property
    def slp_vectorization(self):
        return ffi.lib.LLVMPY_PTOGetSLPVectorization(self)

    @slp_vectorization.setter
    def slp_vectorization(self, value):
        ffi.lib.LLVMPY_PTOSetSLPVectorization(self, value)

    @property
    def loop_unrolling(self):
        return ffi.lib.LLVMPY_PTOGetLoopUnrolling(self)

    @loop_unrolling.setter
    def loop_unrolling(self, value):
        ffi.lib.LLVMPY_PTOSetLoopUnrolling(self, value)

    # // FIXME: Available from llvm16
    # @property
    # def inlining_threshold(self):
    #     return ffi.lib.LLVMPY_PTOGetInlinerThreshold(self)

    # @inlining_threshold.setter
    # def inlining_threshold(self, value):
    #     ffi.lib.LLVMPY_PTOSetInlinerThreshold(self, value)

    def _dispose(self):
        ffi.lib.LLVMPY_DisposePipelineTuningOptions(self)


class TimePassesHandler(ffi.ObjectRef):
    def __init__(self):
        super().__init__(ffi.lib.LLVMPY_CreateTimePassesHandler())

    def _dispose(self):
        ffi.lib.LLVMPY_DisposeTimePassesHandler(self)


class PassBuilder(ffi.ObjectRef):

    def __init__(self, tm, pto):
        super().__init__(ffi.lib.LLVMPY_CreatePassBuilder(tm, pto))
        self._pto = pto
        self._tm = tm
        self._time_passes_handler = None

    def getModulePassManager(self):
        return ModulePassManager(
            ffi.lib.LLVMPY_buildPerModuleDefaultPipeline(
                self, self._pto.speed_level, self._pto.size_level)
        )

    def getFunctionPassManager(self):
        return FunctionPassManager(
            ffi.lib.LLVMPY_buildFunctionSimplificationPipeline(
                self, self._pto.speed_level, self._pto.size_level)
        )

    def start_pass_timing(self):
        """Enable the pass timers.

        Raises
        ------
        RuntimeError
            If pass timing is already enabled.
        """
        if self._time_passes_handler:
            raise RuntimeError("Pass timing can only be done once")
        self._time_passes_handler = TimePassesHandler()
        ffi.lib.LLVMPY_EnableTimePasses(self, self._time_passes_handler)

    def finish_pass_timing(self):
        """Returns the pass timings report and disables the LLVM internal
        timers. Pass timers are enabled by ``start_pass_timing()``. If the
        timers are not enabled, this function will return an empty string.

        Returns
        -------
        res : str
            LLVM generated timing report.
        """

        if not self._time_passes_handler:
            raise RuntimeError("Pass timing is not enabled")

        with ffi.OutputString() as buf:
            ffi.lib.LLVMPY_ReportAndDisableTimePasses(
                self._time_passes_handler, buf)
            return str(buf)

    def _dispose(self):
        ffi.lib.LLVMPY_DisposePassBuilder(self)


# ============================================================================
# FFI

# ModulePassManager

ffi.lib.LLVMPY_CreateNewModulePassManager.restype = ffi.LLVMModulePassManagerRef

ffi.lib.LLVMPY_RunNewModulePassManager.argtypes = [
    ffi.LLVMModulePassManagerRef, ffi.LLVMModuleRef,
    ffi.LLVMPassBuilderRef,]

ffi.lib.LLVMPY_AddVerifierPass.argtypes = [ffi.LLVMModulePassManagerRef,]
ffi.lib.LLVMPY_AddAAEvalPass_module.argtypes = [ffi.LLVMModulePassManagerRef,]
ffi.lib.LLVMPY_AddSimplifyCFGPass_module.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_AddLoopUnrollPass_module.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_AddLoopRotatePass_module.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_AddInstructionCombinePass_module.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_AddJumpThreadingPass_module.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_DisposeNewModulePassManger.argtypes = [
    ffi.LLVMModulePassManagerRef,]

ffi.lib.LLVMPY_AddRefPrunePass_module.argtypes = [
    ffi.LLVMModulePassManagerRef, c_int, c_size_t,
]

# FunctionPassManager

ffi.lib.LLVMPY_CreateNewFunctionPassManager.restype = \
    ffi.LLVMFunctionPassManagerRef

ffi.lib.LLVMPY_RunNewFunctionPassManager.argtypes = [
    ffi.LLVMFunctionPassManagerRef, ffi.LLVMValueRef,
    ffi.LLVMPassBuilderRef,]

ffi.lib.LLVMPY_AddAAEvalPass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddSimplifyCFGPass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddLoopUnrollPass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddLoopRotatePass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddInstructionCombinePass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddJumpThreadingPass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef, c_int,]

ffi.lib.LLVMPY_DisposeNewFunctionPassManger.argtypes = [
    ffi.LLVMFunctionPassManagerRef,]

ffi.lib.LLVMPY_AddRefPrunePass_function.argtypes = [
    ffi.LLVMFunctionPassManagerRef, c_int, c_size_t,
]

# PipelineTuningOptions

ffi.lib.LLVMPY_CreatePipelineTuningOptions.restype = \
    ffi.LLVMPipelineTuningOptionsRef

ffi.lib.LLVMPY_PTOGetLoopInterleaving.restype = c_bool
ffi.lib.LLVMPY_PTOGetLoopInterleaving.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef,]

ffi.lib.LLVMPY_PTOSetLoopInterleaving.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef, c_bool]

ffi.lib.LLVMPY_PTOGetLoopVectorization.restype = c_bool
ffi.lib.LLVMPY_PTOGetLoopVectorization.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef,]

ffi.lib.LLVMPY_PTOSetLoopVectorization.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef, c_bool]

ffi.lib.LLVMPY_PTOGetSLPVectorization.restype = c_bool
ffi.lib.LLVMPY_PTOGetSLPVectorization.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef,]

ffi.lib.LLVMPY_PTOSetSLPVectorization.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef, c_bool]

ffi.lib.LLVMPY_PTOGetLoopUnrolling.restype = c_bool
ffi.lib.LLVMPY_PTOGetLoopUnrolling.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef,]

ffi.lib.LLVMPY_PTOSetLoopUnrolling.argtypes = [
    ffi.LLVMPipelineTuningOptionsRef, c_bool]

ffi.lib.LLVMPY_DisposePipelineTuningOptions.argtypes = \
    [ffi.LLVMPipelineTuningOptionsRef,]

# PassBuilder

ffi.lib.LLVMPY_CreatePassBuilder.restype = ffi.LLVMPassBuilderRef
ffi.lib.LLVMPY_CreatePassBuilder.argtypes = [
    ffi.LLVMTargetMachineRef,
    ffi.LLVMPipelineTuningOptionsRef,
]

ffi.lib.LLVMPY_DisposePassBuilder.argtypes = [ffi.LLVMPassBuilderRef,]

ffi.lib.LLVMPY_CreateTimePassesHandler.restype = \
    ffi.LLVMTimePassesHandlerRef

ffi.lib.LLVMPY_DisposeTimePassesHandler.argtypes = [
    ffi.LLVMTimePassesHandlerRef,]

ffi.lib.LLVMPY_EnableTimePasses.argtypes = [
    ffi.LLVMPassBuilderRef,
    ffi.LLVMTimePassesHandlerRef,
]

ffi.lib.LLVMPY_ReportAndDisableTimePasses.argtypes = [
    ffi.LLVMTimePassesHandlerRef,
    POINTER(c_char_p),
]

# Pipeline builders

ffi.lib.LLVMPY_buildPerModuleDefaultPipeline.restype = \
    ffi.LLVMModulePassManagerRef
ffi.lib.LLVMPY_buildPerModuleDefaultPipeline.argtypes = [
    ffi.LLVMPassBuilderRef, c_int, c_int]

ffi.lib.LLVMPY_buildFunctionSimplificationPipeline.restype = \
    ffi.LLVMFunctionPassManagerRef
ffi.lib.LLVMPY_buildFunctionSimplificationPipeline.argtypes = [
    ffi.LLVMPassBuilderRef, c_int, c_int]
