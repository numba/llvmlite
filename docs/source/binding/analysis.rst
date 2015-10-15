
Analysis Utilities
==================

.. currentmodule:: llvmlite.binding

.. function:: get_function_cfg(func, show_inst=True)

    Return a string of the control-flow graph of the function in DOT
    format. If the input `func` is not a materialized function, the module
    containing the function is parsed to create an actual LLVM module.
    The `show_inst` flag controls whether the instructions of each block
    are printed.unctions.


