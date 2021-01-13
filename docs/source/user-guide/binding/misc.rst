====
Misc
====

.. currentmodule:: llvmlite.binding.ffi

.. function:: register_lock_callback(acq_fn, rel_fn)

    Register callback functions for lock acquire and release.
    ``acq_fn`` and ``exit_fn`` are callables that take no arguments.

.. function:: unregister_lock_callback(acq_fn, rel_fn)

    Remove the registered callback functions for lock acquire and release.
    The arguments are the same as used in ``register_lock_callback()``.
