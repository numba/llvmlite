from ctypes import c_uint, c_bool
from llvmlite.binding import ffi
from llvmlite.binding import passmanagers


def create_pass_manager_builder():
    return PassManagerBuilder()


class OptimizationLevel(ffi.ObjectRef):
    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_PassManagerCreateOptimizationLevel(0, 0)
        ffi.ObjectRef.__init__(self, ptr)


class PassManagerBuilder(ffi.ObjectRef):
    __opt_level__ = 0
    __size_level__ = 0
    __MAM__ = ffi.LLVMModuleAnalysisManager
    __LAM__ = ffi.LLVMLoopAnalysisManager
    __FAM__ = ffi.LLVMFunctionAnalysisManager
    __CGAM__ = ffi.LLVMCGSCCAnalysisManager
    __PIC__ = ffi.LLVMPassInstrumentationCallbacks
    __pipeline_options__ = ffi.LLVMPassBuilderOptionsRef

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_PassManagerBuilderCreate()
        ffi.ObjectRef.__init__(self, ptr)

        self.__MAM__ = ffi.lib.LLVMPY_LLVMModuleAnalysisManagerCreate()
        self.__LAM__ = ffi.lib.LLVMPY_LLVMLoopAnalysisManagerCreate()
        self.__FAM__ = ffi.lib.LLVMPY_LLVMFunctionAnalysisManagerCreate()
        self.__CGAM__ = ffi.lib.LLVMPY_LLVMCGSCCAnalysisManagerCreate()
        self.__PIC__ = ffi.lib.LLVMPY_LLVMPassInstrumentationCallbacksCreate()
        self.__pipeline_options__ = (
            ffi.lib.LLVMPY_PassManagerBuilderOptionsCreate()
        )

    @property
    def opt_level(self):
        """
        The general optimization level as an integer between 0 and 3.
        """
        return self.__opt_level__

    @opt_level.setter
    def opt_level(self, level):
        self.__opt_level__ = level

    @property
    def size_level(self):
        """
        Whether and how much to optimize for size.  An integer between 0 and 2.
        """
        return self.__size_level__

    @size_level.setter
    def size_level(self, size):
        self.__size_level__ = size

    @property
    def inlining_threshold(self):
        """
        The integer threshold for inlining a function into another.  The higher,
        the more likely inlining a function is.  This attribute is write-only.
        """
        raise NotImplementedError("inlining_threshold is write-only")

    @inlining_threshold.setter
    def inlining_threshold(self, threshold):
        ffi.lib.LLVMPY_PassManagerBuilderUseInlinerWithThreshold(
            self.__pipeline_options__, threshold
        )

    @property
    def disable_unroll_loops(self):
        """
        If true, disable loop unrolling.
        """
        return ffi.lib.LLVMPY_PassManagerBuilderGetDisableUnrollLoops(
            self.__pipeline_options__
        )

    @disable_unroll_loops.setter
    def disable_unroll_loops(self, disable=True):
        ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnrollLoops(
            self.__pipeline_options__, disable
        )

    @property
    def loop_vectorize(self):
        """
        If true, allow vectorizing loops.
        """
        return ffi.lib.LLVMPY_PassManagerBuilderGetLoopVectorize(
            self.__pipeline_options__
        )

    @loop_vectorize.setter
    def loop_vectorize(self, enable=True):
        return ffi.lib.LLVMPY_PassManagerBuilderSetLoopVectorize(
            self.__pipeline_options__, enable
        )

    @property
    def slp_vectorize(self):
        """
        If true, enable the "SLP vectorizer", which uses a different algorithm
        from the loop vectorizer.  Both may be enabled at the same time.
        """
        return ffi.lib.LLVMPY_PassManagerBuilderGetSLPVectorize(
            self.__pipeline_options__
        )

    @slp_vectorize.setter
    def slp_vectorize(self, enable=True):
        return ffi.lib.LLVMPY_PassManagerBuilderSetSLPVectorize(
            self.__pipeline_options__, enable
        )

    def _populate_module_pm(self, pm):
        opt_level = OptimizationLevel(
            ffi.lib.LLVMPY_PassManagerCreateOptimizationLevel(
                c_uint(self.__opt_level__), c_uint(self.__size_level__)
            )
        )
        pm.update(
            ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManager(
                self,
                self.__pipeline_options__,
                opt_level,
                pm,
                pm.__MAM__,
                self.__LAM__,
                self.__FAM__,
                self.__CGAM__,
                self.__PIC__,
            )
        )
        pm.__PIC__ = self.__PIC__

    def _populate_function_pm(self, pm):
        opt_level = OptimizationLevel(
            ffi.lib.LLVMPY_PassManagerCreateOptimizationLevel(
                c_uint(self.__opt_level__), c_uint(self.__size_level__)
            )
        )
        pm.update(
            ffi.lib.LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                self,
                self.__pipeline_options__,
                opt_level,
                pm,
                self.__MAM__,
                self.__LAM__,
                pm.__FAM__,
                self.__CGAM__,
                self.__PIC__,
            )
        )
        pm.__PIC__ = self.__PIC__

    def populate(self, pm):
        if isinstance(pm, passmanagers.ModulePassManager):
            self._populate_module_pm(pm)
        elif isinstance(pm, passmanagers.FunctionPassManager):
            self._populate_function_pm(pm)
        else:
            raise TypeError(pm)

    def _dispose(self):
        self._capi.LLVMPY_PassManagerBuilderDispose(
            self, self.__pipeline_options__
        )


# ============================================================================
# FFI

ffi.lib.LLVMPY_PassManagerBuilderCreate.restype = ffi.LLVMPassBuilder

ffi.lib.LLVMPY_LLVMModuleAnalysisManagerCreate.restype = (
    ffi.LLVMModuleAnalysisManager
)
ffi.lib.LLVMPY_LLVMLoopAnalysisManagerCreate.restype = (
    ffi.LLVMLoopAnalysisManager
)
ffi.lib.LLVMPY_LLVMFunctionAnalysisManagerCreate.restype = (
    ffi.LLVMFunctionAnalysisManager
)
ffi.lib.LLVMPY_LLVMCGSCCAnalysisManagerCreate.restype = (
    ffi.LLVMCGSCCAnalysisManager
)
ffi.lib.LLVMPY_LLVMPassInstrumentationCallbacksCreate.restype = (
    ffi.LLVMPassInstrumentationCallbacks
)


ffi.lib.LLVMPY_PassManagerBuilderOptionsCreate.restype = (
    ffi.LLVMPassBuilderOptionsRef
)

ffi.lib.LLVMPY_PassManagerBuilderDispose.argtypes = [
    ffi.LLVMPassBuilder,
    ffi.LLVMPassBuilderOptionsRef,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManager.argtypes = [
    ffi.LLVMPassBuilder,
    ffi.LLVMPassBuilderOptionsRef,
    ffi.LLVMOptimizationLevel,
    ffi.LLVMModulePassManager,
    ffi.LLVMModuleAnalysisManager,
    ffi.LLVMLoopAnalysisManager,
    ffi.LLVMFunctionAnalysisManager,
    ffi.LLVMCGSCCAnalysisManager,
    ffi.LLVMPassInstrumentationCallbacks,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManager.restype = (
    ffi.LLVMModulePassManager
)

ffi.lib.LLVMPY_PassManagerBuilderPopulateFunctionPassManager.argtypes = [
    ffi.LLVMPassBuilder,
    ffi.LLVMPassBuilderOptionsRef,
    ffi.LLVMOptimizationLevel,
    ffi.LLVMFunctionPassManager,
    ffi.LLVMModuleAnalysisManager,
    ffi.LLVMLoopAnalysisManager,
    ffi.LLVMFunctionAnalysisManager,
    ffi.LLVMCGSCCAnalysisManager,
    ffi.LLVMPassInstrumentationCallbacks,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateFunctionPassManager.restype = (
    ffi.LLVMFunctionPassManager
)

ffi.lib.LLVMPY_PassManagerCreateOptimizationLevel.restype = (
    ffi.LLVMOptimizationLevel
)
ffi.lib.LLVMPY_PassManagerCreateOptimizationLevel.argtypes = [c_uint, c_uint]

# Unsigned int PassManagerBuilder properties

for _func in (ffi.lib.LLVMPY_PassManagerBuilderUseInlinerWithThreshold,):
    _func.argtypes = [ffi.LLVMPassBuilderOptionsRef, c_uint]


for _func in (
    ffi.lib.LLVMPY_PassManagerBuilderGetOptLevel,
    ffi.lib.LLVMPY_PassManagerBuilderGetSizeLevel,
):
    _func.argtypes = [ffi.LLVMOptimizationLevel]
    _func.restype = c_uint

# Boolean PassManagerBuilder properties

for _func in (
    ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnrollLoops,
    ffi.lib.LLVMPY_PassManagerBuilderSetLoopVectorize,
    ffi.lib.LLVMPY_PassManagerBuilderSetSLPVectorize,
):
    _func.argtypes = [ffi.LLVMPassBuilderOptionsRef, c_bool]

for _func in (
    ffi.lib.LLVMPY_PassManagerBuilderGetDisableUnrollLoops,
    ffi.lib.LLVMPY_PassManagerBuilderGetLoopVectorize,
    ffi.lib.LLVMPY_PassManagerBuilderGetSLPVectorize,
):
    _func.argtypes = [ffi.LLVMPassBuilderOptionsRef]
    _func.restype = c_bool
