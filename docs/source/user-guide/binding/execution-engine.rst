================
Execution engine
================

.. currentmodule:: llvmlite.binding


The execution engine is where actual code generation and execution happen. At
present a single execution engine, ``MCJIT``, is exposed.


Functions
=========

* .. function:: create_mcjit_compiler(module, target_machine, use_lmm=None)

     Create a MCJIT-powered engine from the given *module* and
     *target_machine*.

     *lmm* controls whether the llvmlite memory manager is used. If not
     supplied, the default choice for the platform will be used (``True`` on
     64-bit ARM systems, ``False`` otherwise).

     * *module* does not need to contain any code.
     * Returns a :class:`ExecutionEngine` instance.


* .. function:: check_jit_execution()

     Ensure that the system allows creation of executable memory
     ranges for JIT-compiled code. If some security mechanism
     such as SELinux prevents it, an exception is raised.
     Otherwise the function returns silently.

     Calling this function early can help diagnose system
     configuration issues, instead of letting JIT-compiled
     functions crash mysteriously.


The ExecutionEngine class
=========================

.. class:: ExecutionEngine

   A wrapper around an LLVM execution engine. The following
   methods and properties are available:

   * .. method:: add_module(module)

        Add the *module*---a :class:`ModuleRef` instance---for
        code generation. When this method is called, ownership
        of the module is transferred to the execution engine.

   * .. method:: finalize_object()

        Make sure all modules owned by the execution engine are
        fully processed and usable for execution.

   * .. method:: get_function_address(name)

        Return the address of the function *name* as an integer.
        It's a fatal error in LLVM if the symbol of *name* doesn't exist.

   * .. method:: get_global_value_address(name)

        Return the address of the global value *name* as an
        integer.
        It's a fatal error in LLVM if the symbol of *name* doesn't exist.

   * .. method:: remove_module(module)

        Remove the *module*---a :class:`ModuleRef` instance---from
        the modules owned by the execution engine. This allows
        releasing the resources owned by the module without
        destroying the execution engine.

    * .. method:: add_object_file(object_file)

        Add the symbols from the specified object file to the execution
        engine.

        * *object_file* str or :class:`ObjectFileRef`: a path to the object file
            or a object file instance. Object file instance is not usable after this
            call.

   * .. method:: set_object_cache(notify_func=None, getbuffer_func=None)

        Set the object cache callbacks for this engine.

        * *notify_func*, if given, is called whenever the engine
          has finished compiling a module. It is passed the
          ``(module, buffer)`` arguments:

          * *module* is a :class:`ModuleRef` instance.
          * *buffer* is a bytes object of the code generated for
            the module.

          The return value is ignored.

        * *getbuffer_func*, if given, is called before the engine
          starts compiling a module. It is passed an argument,
          *module*, a :class:`ModuleRef` instance of the module
          being compiled.

          * It can return ``None``, in which case the module
            is compiled normally.
          * It can return a bytes object of native code for the
            module, which bypasses compilation entirely.

   * .. attribute:: target_data

        The :class:`TargetData` used by the execution engine.
