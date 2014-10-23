from llvmlite import binding as llvm
from collections import namedtuple

def build_pass_managers(**kws):
    pm = llvm.create_module_pass_manager()
    if kws.get('fpm', True):
        # XXX: skipped for now
        fpm = DummyFPM()
    else:
        fpm = None

    with llvm.create_pass_manager_builder() as pmb:
        pmb.opt_level = kws.get('opt', 2)
        pmb.populate(pm)
        return namedtuple("pms", ['pm', 'fpm'])(pm=pm, fpm=fpm)


class DummyFPM(object):
    def initialize(self, *args, **kws):
        pass

    def finalize(self, *args, **kws):
        pass

    def run(self, *args, **kws):
        pass


