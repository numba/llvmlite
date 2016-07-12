
Execution engine
================

.. currentmodule:: llvmlite.binding


The execution engine is where actual code generation and execution happens.
The currently supported LLVM version (LLVM 3.8) exposes one execution engine,
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

   .. method:: get_pointer_to_function(gv)

      .. warning::
         This function is deprecated.  User should use
         :meth:`ExecutionEngine.get_function_address` and
         :meth:`ExecutionEngine.get_global_value_address` instead

      Return the address of the function value *gv*, as an integer.  The
      value should have been looked up on one of the modules owned by
      the execution engine.

      .. note::
         This method may implicitly generate code for the object being
         looked up.

      .. note::
         This function is formerly an alias to ``get_pointer_to_global()``,
         which is now removed because it returns an invalid address in MCJIT
         when given a non-function global value.

   .. method:: get_function_address(name)

      Return the address of the function named *name* as an integer.

   .. method:: get_global_value_address(name)

      Return the address of the global value named *name* as an integer.

   .. method:: remove_module(module)

      Remove the *module* (a :class:`ModuleRef` instance) from the modules
      owned by the execution engine.  This allows releasing the resources
      owned by the module without destroying the execution engine.

   .. method:: set_object_cache(notify_func=None, getbuffer_func=None)

      Set the object cache callbacks for this engine.

      *notify_func*, if given, is called whenever the engine has finished
      compiling a module.  It is passed two arguments ``(module, buffer)``.
      The first argument *module* is a :class:`ModuleRef` instance.
      The second argument *buffer* is a bytes object of the code generated
      for the module.  The return value is ignored.

      *getbuffer_func*, if given, is called before the engine starts
      compiling a module.  It is passed one argument, *module*, a
      :class:`ModuleRef` instance of the module being compiled.
      The function can return ``None``, in which case the module
      will be compiled normally.  Or it can return a bytes object of
      native code for the module, which will bypass compilation entirely.

   .. attribute:: target_data

      The :class:`TargetData` used by the execution engine.
