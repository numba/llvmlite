
Analysis Utilities
==================

.. currentmodule:: llvmlite.binding

.. function:: get_function_cfg(func, show_inst=True)

    Return a string of the control-flow graph of the function in DOT
    format. If the input `func` is not a materialized function, the module
    containing the function is parsed to create an actual LLVM module.
    The `show_inst` flag controls whether the instructions of each block
    are printed.unctions.

.. function:: view_dot_graph(graph, filename=None, view=False)

    View the given DOT source.  If view is True, the image is rendered
    and viewed by the default application in the system.  The file path of
    the output is returned.  If view is False, a graphviz.Source object is
    returned.  If view is False and the environment is in a IPython session,
    an IPython image object is returned and can be displayed inline in the
    notebook.

    .. note:: This function requires the graphviz package.
