"""
Useful options to debug LLVM passes

llvm.set_option("test", "-debug-pass=Details")
llvm.set_option("test", "-debug-pass=Executions")
llvm.set_option("test", "-debug-pass=Arguments")
llvm.set_option("test", "-debug-pass=Structure")
llvm.set_option("test", "-debug-only=loop-vectorize")
llvm.set_option("test", "-help-hidden")

"""

from llvmlite import binding as llvm
from collections import namedtuple


def _inlining_threshold(optlevel, sizelevel=0):
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


def create_pass_manager_builder(opt=2, loop_vectorize=False,
                                slp_vectorize=False):
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = opt
    pmb.loop_vectorize = loop_vectorize
    pmb.slp_vectorize = slp_vectorize
    pmb.inlining_threshold = _inlining_threshold(opt)
    return pmb


def build_pass_managers(**kws):
    mod = kws.get('mod')
    if not mod:
        raise NameError("module must be provided")

    pm = llvm.create_module_pass_manager()

    if kws.get('fpm', True):
        assert isinstance(mod, llvm.ModuleRef)
        fpm = llvm.create_function_pass_manager(mod)
    else:
        fpm = None

    with llvm.create_pass_manager_builder() as pmb:
        pmb.opt_level = opt = kws.get('opt', 2)
        pmb.loop_vectorize = kws.get('loop_vectorize', False)
        pmb.slp_vectorize = kws.get('slp_vectorize', False)
        pmb.inlining_threshold = _inlining_threshold(optlevel=opt)

        if mod:
            tli = llvm.create_target_library_info(mod.triple)
            if kws.get('nobuiltins', False):
                # Disable all builtins (-fno-builtins)
                tli.disable_all()
            else:
                # Disable a list of builtins given
                for k in kws.get('disable_builtins', ()):
                    libf = tli.get_libfunc(k)
                    tli.set_unavailable(libf)

            tli.add_pass(pm)
            if fpm is not None:
                tli.add_pass(fpm)

        tm = kws.get('tm')
        if tm:
            tm.add_analysis_passes(pm)
            if fpm is not None:
                tm.add_analysis_passes(fpm)

        pmb.populate(pm)
        if fpm is not None:
            pmb.populate(fpm)

        return namedtuple("pms", ['pm', 'fpm'])(pm=pm, fpm=fpm)

