"""
Useful options to debug LLVM passes

llvm.set_option("test", "-debug-pass=Details")
llvm.set_option("test", "-debug-pass=Executions")
llvm.set_option("test", "-debug-pass=Arguments")
llvm.set_option("test", "-debug-pass=Structure")
llvm.set_option("test", "-debug-only=loop-vectorize")
llvm.set_option("test", "-help-hidden")

"""

from __future__ import annotations

import warnings
from collections import namedtuple

from llvmlite import binding as llvm

warnings.warn(
    "The module `llvmlite.llvmpy.passes` is deprecated and will be removed in "
    "the future. If you are using this code, it should be inlined into your "
    "own project."
)
from typing import Any, NamedTuple, Union

from typing_extensions import Literal

from llvmlite import binding as llvm
from llvmlite.binding.passmanagers import FunctionPassManager, PassManager
from llvmlite.binding.transforms import PassManagerBuilder

pms = NamedTuple(
    "pms", [("pm", PassManager), ("fpm", Union[FunctionPassManager, None])]
)


def _inlining_threshold(optlevel: int, sizelevel: int = 0) -> int:
    # Refer http://llvm.org/docs/doxygen/html/InlineSimple_8cpp_source.html
    if optlevel > 2:
        return 275
    # -Os
    if sizelevel == 1:
        return 75
    # -Oz
    if sizelevel == 2:
        return 25
    return 225


def create_pass_manager_builder(
    opt: Literal[0, 1, 2, 3] = 2,
    loop_vectorize: bool = False,
    slp_vectorize: bool = False,
) -> PassManagerBuilder:
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = opt
    pmb.loop_vectorize = loop_vectorize
    pmb.slp_vectorize = slp_vectorize
    pmb.inlining_threshold = _inlining_threshold(opt)
    return pmb


def build_pass_managers(**kws: dict[str, Any]) -> pms:
    mod = kws.get("mod")
    if not mod:
        raise NameError("module must be provided")

    pm = llvm.create_module_pass_manager()

    if kws.get("fpm", True):
        assert isinstance(mod, llvm.ModuleRef)
        fpm = llvm.create_function_pass_manager(mod)
    else:
        fpm = None

    with llvm.create_pass_manager_builder() as pmb:
        pmb.opt_level = opt = kws.get("opt", 2)  # type: ignore
        pmb.loop_vectorize = kws.get("loop_vectorize", False)  # type: ignore
        pmb.slp_vectorize = kws.get("slp_vectorize", False)  # type: ignore
        pmb.inlining_threshold = _inlining_threshold(optlevel=opt)  # type: ignore

        if mod:
            tli = llvm.create_target_library_info(mod.triple)  # type: ignore
            if kws.get("nobuiltins", False):
                # Disable all builtins (-fno-builtins)
                tli.disable_all()  # type: ignore
            else:
                # Disable a list of builtins given
                for k in kws.get("disable_builtins", ()):
                    libf = tli.get_libfunc(k)  # type: ignore
                    tli.set_unavailable(libf)  # type: ignore

            tli.add_pass(pm)  # type: ignore
            if fpm is not None:
                tli.add_pass(fpm)  # type: ignore

        tm = kws.get("tm")
        if tm:
            tm.add_analysis_passes(pm)  # type: ignore
            if fpm is not None:
                tm.add_analysis_passes(fpm)  # type: ignore

        pmb.populate(pm)  # type: ignore
        if fpm is not None:
            pmb.populate(fpm)  # type: ignore

        return pms(pm=pm, fpm=fpm)
