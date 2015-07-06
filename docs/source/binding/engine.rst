
Execution engine
================

.. currentmodule:: llvmlite.binding


The execution engine is where actual code generation and execution happens.
The currently supported LLVM version (LLVM 3.6) exposes one execution engine,
named MCJIT.


Functions
---------

.. function:: create_mcjit_compiler(module, target_machine)

   Create a MCJIT-powered engine from the given *module* and
   *target_machine*.  A :class:`ExecutionEngine` instance is returned.
   The *module* need not contain any code.


.. function:: check_jit_execution()

   Ensure the system allows creation of executable memory ranges for
   JIT-compiled code.  If some security mechanism (such as SELinux) prevents
   it, an exception is raised.  Otherwise the function returns silently.

   Calling this function early can help diagnose system configuration issues,
   instead of letting JIT-compiled functions crash mysteriously.


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

