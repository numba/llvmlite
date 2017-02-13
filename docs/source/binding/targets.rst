
Target information
==================

.. currentmodule:: llvmlite.binding

Target information allows you to inspect and modify aspects of the code
generation, such as which CPU is targetted or what optimization level is
desired.

Minimal use of this module would be to create a :class:`TargetMachine`
for later use in code generation::

   from llvmlite import binding
   target = binding.Target.from_default_triple()
   target_machine = target.create_target_machine()


Functions
---------

.. function:: get_default_triple()

   Return the default target triple LLVM is configured to produce code for,
   as a string.  This represents the host's architecture and platform.

.. function:: get_process_triple()

   Return a target triple suitable for generating code for the current process.
   An example when the default triple from ``get_default_triple()`` is not be
   suitable is when LLVM is compiled for 32-bit but the process is executing
   in 64-bit mode.

.. function:: get_object_format(triple=None)

   Get the object format for the given *triple* string (or the default
   triple if None).  A string is returned such as ``"ELF"``, ``"COFF"``
   or ``"MachO"``.

.. function:: get_host_cpu_name()

   Get the name of the host's CPU as a string.  You can use the
   return value with :meth:`Target.create_target_machine()`.

.. function:: get_host_cpu_features()

   Returns a dictionary-like object indicating the CPU features for current
   architecture and whether they are enabled for this CPU.  The key-value pairs
   are the feature name as string and a boolean indicating whether the feature
   is available.  The returned value is an instance of ``FeatureMap`` class,
   which adds a new method ``.flatten()`` for returning a string suitable for
   use as the "features" argument to :meth:`Target.create_target_machine()`.

   If LLVM has not implemented this feature or it fails to get the information,
   this function will raise a ``RuntimeError`` exception.


.. function:: create_target_data(data_layout)

   Create a :class:`TargetData` representing the given *data_layout* (a
   string).



Classes
-------

.. class:: TargetData

   A class providing functionality around a given data layout.  It
   specifies how the different types are to be represented in memory.
   Use :func:`create_target_data` to instantiate.

   .. method:: get_abi_size(type)

      Get the ABI-mandated size of the LLVM *type* (as returned by
      :attr:`ValueRef.type`).  An integer is returned.

   .. method:: get_pointee_abi_size(type)

      Similar to :meth:`get_abi_size`, but assumes *type* is a LLVM
      pointer type, and returns the ABI-mandated size of the type pointed
      to by.  This is useful for global variables (whose type is really
      a pointer to the declared type).

   .. method:: get_pointee_abi_alignment(type)

      Similar to :meth:`get_pointee_abi_size`, but return the ABI-mandated
      alignment rather than the ABI size.


.. class:: Target

   A class representing a compilation target.  The following factories
   are provided:

   .. classmethod:: from_triple(triple)

      Create a new :class:`Target` instance for the given *triple* string
      denoting the target platform.

   .. classmethod:: from_default_triple()

      Create a new :class:`Target` instance for the default platform
      LLVM is configured to produce code for.  This is equivalent to
      calling ``Target.from_triple(get_default_triple())``

   The following methods and attributes are available:

   .. attribute:: description

      A description of the target.

   .. attribute:: name

      The name of the target.

   .. attribute:: triple

      The triple (a string) uniquely identifying the target, for
      example ``"x86_64-pc-linux-gnu"``.

   .. method:: create_target_machine(cpu='', features='', \
                      opt=2, reloc='default', codemodel='jitdefault')

      Create a new :class:`TargetMachine` instance for this target
      and with the given options.  *cpu* is an optional CPU name to
      specialize for.  *features* is a comma-separated list of target-specific
      features to enable or disable.  *opt* is the optimization level,
      from 0 to 3.  *reloc* is the relocation model.  *codemodel* is
      the code model.  The defaults for *reloc* and *codemodel* are
      appropriate for JIT compilation.

      .. tip::
         To list the available CPUs and features for a target,
         execute ``llc -mcpu=help`` on the command line.


.. class:: TargetMachine

   A class holding all the settings necessary for proper code generation
   (including target information and compiler options).  Instantiate
   using :meth:`Target.create_target_machine`.

   .. method:: add_analysis_passes(pm)

      Register analysis passes for this target machine with the
      :class:`PassManager` instance *pm*.

   .. method:: emit_object(module)

      Represent the compiled *module* (a :class:`ModuleRef` instance) as
      a code object, suitable for use with the platform's linker.
      A bytestring is returned.

   .. method:: set_asm_verbosity(is_verbose)

      Set whether this target machine will emit assembly with human-readable
      comments describing control flow, debug information, and so on.

   .. method:: emit_assembly(module)

      Return the compiled *module*'s native assembler, as a string.

      :func:`initialize_native_asmprinter()` must have been called first.

   .. attribute:: target_data

      The :class:`TargetData` associated with this target machine.


.. class:: FeatureMap

   For storing processor feature information in a dictionary-like object.
   This class extends ``dict`` and only adds the ``.flatten()`` method.

   .. method:: flatten(sort=True)

      Returns a string representation of the stored information that is suitable
      for use in the "features" argument of
      :meth:`Target.create_target_machine()`.
      If ``sort`` keyword argument is True (the default), the features are
      sorted by name to give a stable ordering between python session.
