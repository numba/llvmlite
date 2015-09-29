
Analysis references
===================

.. currentmodule:: llvmlite.binding


A few LLVM analysis are exposed as utility functions.

.. function:: view_function_cfg(fn)

    Generate a DOT file for the control flow graph of the given function
    with all instructions listed.  The function `fn` can be either a
    materialized  `llvmlite.binding.ValueRef` or a unmaterialized
    ``llvmlite.ir.Function`` instance.

.. function:: view_function_cfg_only(fn)

    Like ``view_function_cfg(fn)`` but the generated DOT file does
    not list the instructions.
