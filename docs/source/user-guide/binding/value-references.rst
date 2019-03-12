================
Value references
================

.. currentmodule:: llvmlite.binding

A value reference is a wrapper around an LLVM value for you to
inspect. You cannot create a value reference yourself. You get them
from methods of the :class:`ModuleRef` and :class:`ValueRef` classes.

Enumerations
------------

.. class:: Linkage

   The linkage types allowed for global values are:

   * .. data:: external
   * .. data:: available_externally
   * .. data:: linkonce_any
   * .. data:: linkonce_odr
   * .. data:: linkonce_odr_autohide
   * .. data:: weak_any
   * .. data:: weak_odr
   * .. data:: appending
   * .. data:: internal
   * .. data:: private
   * .. data:: dllimport
   * .. data:: dllexport
   * .. data:: external_weak
   * .. data:: ghost
   * .. data:: common
   * .. data:: linker_private
   * .. data:: linker_private_weak


.. class:: Visibility

   The visibility styles allowed for global values are:

   * .. data:: default
   * .. data:: hidden
   * .. data:: protected


.. class:: StorageClass

   The storage classes allowed for global values are:

   * .. data:: default
   * .. data:: dllimport
   * .. data:: dllexport


The ValueRef class
------------------

.. class:: ValueRef

   A wrapper around an LLVM value. The attributes available are:

   * .. attribute:: is_declaration

        * ``True``---The global value is a mere declaration.
        * ``False``---The global value is defined in the given 
          module.

   * .. attribute:: linkage

        The linkage type---a :class:`Linkage` instance---for 
        this value. This attribute can be set.

   * .. attribute:: module

        The module---a :class:`ModuleRef` instance---that this
        value is defined in.

   * .. attribute:: function

        The function---a :class:`ValueRef` instance---that this
        value is defined in.

   * .. attribute:: block

        The basic block---a :class:`ValueRef` instance---that this
        value is defined in.

   * .. attribute:: instruction

        The instruction---a :class:`ValueRef` instance---that this
        value is defined in.

   * .. attribute:: name

        This value's name, as a string. This attribute can be set.

   * .. attribute:: type

        This value's LLVM type as :class:`TypeRef` object.

   * .. attribute:: storage_class

        The storage 
        class---a :class:`StorageClass` instance---for 
        this value. This attribute can be set.

   * .. attribute:: visibility

        The visibility 
        style---a :class:`Visibility` instance---for 
        this value. This attribute can be set.

   * .. attribute:: blocks

        An iterator over the basic blocks in this function.
        Each block is a :class:`ValueRef` instance.

   * .. attribute:: arguments

        An iterator over the arguments of this function.
        Each argument is a :class:`ValueRef` instance.

   * .. attribute:: instructions

        An iterator over the instructions in this basic block.
        Each instruction is a :class:`ValueRef` instance.

   * .. attribute:: operands

        An iterator over the operands in this instruction.
        Each operand is a :class:`ValueRef` instance.

   * .. attribute:: opcode

        The instruction's opcode, as a string.

   * .. attribute:: attributes

        An iterator over the attributes in this value.
        Each attribute is a :class:`bytes` instance.
        Values that have attributes are: function, argument (and
        others for which attributes support has not been implemented)

   * .. attribute:: is_global

        The value is a global variable.

   * .. attribute:: is_function

        The value is a function.

   * .. attribute:: is_argument

        The value is a function's argument.

   * .. attribute:: is_block

        The value is a function's basic block.

   * .. attribute:: is_instruction

        The value is a basic block's instruction.

   * .. attribute:: is_operand

        The value is a instruction's operand.
