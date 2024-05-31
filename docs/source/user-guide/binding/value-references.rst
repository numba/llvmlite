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


.. class:: ValueKind

   The value kinds allowed are:

   * .. data:: argument
   * .. data:: basic_block
   * .. data:: memory_use
   * .. data:: memory_def
   * .. data:: memory_phi
   * .. data:: function
   * .. data:: global_alias
   * .. data:: global_ifunc
   * .. data:: global_variable
   * .. data:: block_address
   * .. data:: constant_expr
   * .. data:: constant_array
   * .. data:: constant_struct
   * .. data:: constant_vector
   * .. data:: undef_value
   * .. data:: constant_aggregate_zero
   * .. data:: constant_data_array
   * .. data:: constant_data_vector
   * .. data:: constant_int
   * .. data:: constant_fp
   * .. data:: constant_pointer_null
   * .. data:: constant_token_none
   * .. data:: metadata_as_value
   * .. data:: inline_asm
   * .. data:: instruction
   * .. data:: poison_value


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

   * .. attribute:: value_kind

        The LLVM value kind---a :class:`ValueKind` instance---for
        this value.

   * .. attribute:: blocks

        An iterator over the basic blocks in this function.
        Each block is a :class:`ValueRef` instance.

   * .. attribute:: arguments

        An iterator over the arguments of this function.
        Each argument is a :class:`ValueRef` instance.

   * .. attribute:: instructions

        An iterator over the instructions in this basic block.
        Each instruction is a :class:`ValueRef` instance.

   * .. attribute:: incoming_blocks

        An iterator over the incoming blocks of a phi instruction.
        Each block is a :class:`ValueRef` instance.

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

   * .. attribute:: is_constant

        The value is a constant.

   * .. method:: get_constant_value(self, signed_int=False, round_fp=False)

        Return the constant value, either as a literal (for example, int
        or float) when supported, or as a string otherwise. Keyword arguments
        specify the preferences during conversion:

           * If ``signed_int`` is True and the constant is an integer, returns a
             signed integer.
           * If ``round_fp`` True and the constant is a floating point value,
             rounds the result upon accuracy loss (e.g., when querying an fp128
             value). By default, raises an exception on accuracy loss.
