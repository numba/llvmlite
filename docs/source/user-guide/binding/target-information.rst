==================
Target information
==================

.. currentmodule:: llvmlite.binding

Target information allows you to inspect and modify aspects of
the code generation, such as which CPU is targeted or what
optimization level is desired.

Minimal use of this module would be to create a
:class:`TargetMachine` for later use in code generation.

EXAMPLE::

   from llvmlite import binding
   target = binding.Target.from_default_triple()
   target_machine = target.create_target_machine()

Functions
==========

* .. function:: get_default_triple()

     Return a string representing the default target triple that
     LLVM is configured to produce code for. This represents the
     host's architecture and platform.

* .. function:: get_process_triple()

     Return a target triple suitable for generating code for the
     current process.

     EXAMPLE: The default triple from ``get_default_triple()``
     is not suitable when LLVM is compiled for 32-bit, but the
     process is executing in 64-bit mode.

* .. function:: get_object_format(triple=None)

     Get the object format for the given *triple* string, or the
     default triple if ``None``. Returns a string such as
     ``"ELF"``, ``"COFF"`` or ``"MachO"``.

* .. function:: get_host_cpu_name()

     Get the name of the host's CPU as a string. You can use the
     return value with :meth:`Target.create_target_machine()`.

* .. function:: get_host_cpu_features()

     Return a dictionary-like object indicating the CPU features
     for the current architecture and whether they are enabled
     for this CPU.

     The key-value pairs contain the feature name
     as a string and a boolean indicating whether the feature is
     available.

     The returned value is an instance of the
     ``FeatureMap`` class, which adds a new method
     ``.flatten()`` for returning a string suitable for use
     as the ``features`` argument to
     :meth:`Target.create_target_machine()`.

     If LLVM has not implemented this feature or it fails to get
     the information, a ``RuntimeError`` exception is raised.

* .. function:: create_target_data(data_layout)

     Create a :class:`TargetData` representing the given
     *data_layout* string.

Classes
=======

.. class:: TargetData

   Provides functionality around a given data layout. It
   specifies how the different types are to be represented in
   memory. Use :func:`create_target_data` to instantiate.

   * .. method:: get_abi_size(type)

        Get the ABI-mandated size of a :class:`TypeRef` object.
        Returns an integer.

   * .. method:: get_pointee_abi_size(type)

        Similar to :meth:`get_abi_size`, but assumes that *type* is
        an LLVM pointer type and returns the ABI-mandated size of
        the type pointed to. This is useful for a global
        variable, whose type is really a pointer to the declared
        type.

   * .. method:: get_pointee_abi_alignment(type)

        Similar to :meth:`get_pointee_abi_size`, but returns the
        ABI-mandated alignment rather than the ABI size.

   * .. method:: get_element_offset(type, position)

        Computes the byte offset of the struct element at position.

.. class:: Target

   Represents a compilation target. The following factories
   are provided:

   * .. classmethod:: from_triple(triple)

        Create a new :class:`Target` instance for the given
        *triple* string denoting the target platform.

   * .. classmethod:: from_default_triple()

        Create a new :class:`Target` instance for the default
        platform that LLVM is configured to produce code for.
        This is equivalent to calling
        ``Target.from_triple(get_default_triple())``.

   The following attributes and methods are available:

   * .. attribute:: description

        A description of the target.

   * .. attribute:: name

        The name of the target.

   * .. attribute:: triple

        A string that uniquely identifies the target.

        EXAMPLE: ``"x86_64-pc-linux-gnu"``

   * .. method:: create_target_machine(cpu='', features='', \
          opt=2, reloc='default', codemodel='jitdefault', \
          abiname='')

        Create a new :class:`TargetMachine` instance for this
        target and with the given options:

        * *cpu* is an optional CPU name to specialize for.
        * *features* is a comma-separated list of target-specific
          features to enable or disable.
        * *opt* is the optimization level, from 0 to 3.
        * *reloc* is the relocation model.
        * *codemodel* is the code model.
        * *abiname* is the name of the ABI.

        The defaults for reloc and codemodel are appropriate for
        JIT compilation.

        TIP: To list the available CPUs and features for a
        target, run the command ``llc -mcpu=help``.

.. class:: TargetMachine

   Holds all the settings necessary for proper code generation,
   including target information and compiler options. Instantiate
   using :meth:`Target.create_target_machine`.

   * .. method:: add_analysis_passes(pm)

        Register analysis passes for this target machine with the
        :class:`PassManager` instance *pm*.

   * .. method:: emit_object(module)

        Represent the compiled *module*---a :class:`ModuleRef`
        instance---as a code object that is suitable for use
        with the platform's linker. Returns a bytestring.

   * .. method:: set_asm_verbosity(is_verbose)

        Set whether this target machine emits assembly with
        human-readable comments, such as those describing control
        flow or debug information.

   * .. method:: emit_assembly(module)

        Return a string representing the compiled *module*'s native
        assembler. You must first call
        :func:`initialize_native_asmprinter()`.

   * .. attribute:: target_data

        The :class:`TargetData` associated with this target
        machine.


.. class:: FeatureMap

   Stores processor feature information in a dictionary-like
   object. This class extends ``dict`` and adds only the
   ``.flatten()`` method.

   .. method:: flatten(sort=True)

      Returns a string representation of the stored information
      that is suitable for use in the ``features`` argument of
      :meth:`Target.create_target_machine()`.

      If the ``sort`` keyword argument is
      ``True``---the default---the features are sorted by name
      to give a stable ordering between Python sessions.
