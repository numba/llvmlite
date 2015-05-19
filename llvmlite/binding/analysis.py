from __future__ import absolute_import

from .module import parse_assembly
from .value import ValueRef

__all__ = [
'view_function_cfg',
]


def view_function_cfg(fn):
    """
    Generate a DOT file of the Function's control flow graph.
    Argument ``fn`` can be either a materialized ``ValueRef`` instance of a
    function or a unmaterialized ``llvmlite.ir.Function`` instance.
    """

    if not isinstance(fn, ValueRef):
        fn = parse_assembly(str(fn.module)).get_function(fn.name)
    fn.view_cfg()



def view_function_cfg_only(fn):
    """
    Similar to ``view_function_cfg`` but instructions are not printed.
    """

    if not isinstance(fn, ValueRef):
        fn = parse_assembly(str(fn.module)).get_function(fn.name)
    fn.view_cfg_only()
