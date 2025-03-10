============
Pass Timings
============

.. currentmodule:: llvmlite.binding

LLVM provides functionality to time optimization and analysis passes.

New Pass Manager APIs
=====================

See :meth:`PassBuilder.start_pass_timing` and
:meth:`PassBuilder.finish_pass_timing` in :doc:`optimization-passes`.

Legacy Pass Manager APIs
========================


.. function:: set_time_passes(enable)

    Enable or disable the pass timers.


.. function:: report_and_reset_timings()

    Returns the pass timings report and resets the LLVM internal timers.

    Pass timers are enabled by ``set_time_passes()``. If the timers are not
    enabled, this function will return an empty string.
