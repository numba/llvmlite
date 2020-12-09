============
Pass Timings
============

.. currentmodule:: llvmlite.binding

.. function:: set_time_passes(enable)

    Enable or disable pass timers.


.. function:: report_and_reset_timings()

    Returns pass timings report and reset LLVM internal timers.

    Pass timers are enabled by ``set_time_passes()``. If the timers are not
    enabled, this function will return an empty string.
