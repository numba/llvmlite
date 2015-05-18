
Execution engine
================

.. currentmodule:: llvmlite.binding


The execution engine is where actual code generation and execution happens.
In the currently supported LLVM version (LLVM 3.5), there are two
execution engines: MCJIT and the "old JIT".  Starting from LLVM 3.6,
the "old JIT" is removed.  llvmlite exposes the same API for both, but
they may have slightly different behaviour.


Factory functions
-----------------

.. function:: create_mcjit_compiler(module, target_machine)

   Create a MCJIT-powered engine from the given *module* and
   *target_machine*.  A :class:`ExecutionEngine` instance is returned.
   The *module* need not contain any code.


.. function:: create_jit_compiler_with_tm(module, target_machine)

   Create a "old JIT"-powered engine from the given *module* and
   *target_machine*.  A :class:`ExecutionEngine` instance is returned.
   The *module* need not contain any code.


The ExecutionEngine class
-------------------------

.. class:: ExecutionEngine

   A wrapper around a LLVM execution engine.  The following methods and
   properties are available:

   .. method:: add_module(module)

      Add the *module* (a :class:`ModuleRef` instance) for code generation.
      When this method is called, ownership of the module is transferred
      to the execution engine.

   .. method:: finalize_object()

      Make sure all modules owned by the execution engine are fully processed
      and "usable" for execution.

   .. method:: get_pointer_to_global(gv)

      Return the address of the global value *gv*, as an integer.  The
      value should have been looked up on one of the modules owned by
      the execution engine.

      .. note::
         This method may implicitly generate code for the object being
         looked up.

   .. method:: remove_module(module)

      Remove the *module* (a :class:`ModuleRef` instance) from the modules
      owned by the execution engine.  This allows releasing the resources
      owned by the module without destroying the execution engine.

   .. attribute:: target_data

      The :class:`TargetData` used by the execution engine.

