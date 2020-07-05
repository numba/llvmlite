.. _ir-values:

======
Values
======

.. currentmodule:: llvmlite.ir


.. contents::
   :local:
   :depth: 1

A :ref:`module` consists mostly of values.

.. data:: Undefined

   An undefined value, mapping to LLVM's ``undef``.


.. class:: Value

   The base class for all IR values.


.. class:: Constant(typ, constant)

   A literal value.

   * *typ* is the type of the represented value---a
     :class:`~llvmlite.ir.Type` instance.

   * *constant* is the Python value to be represented.

   Which Python types are allowed for *constant* depends on *typ*:

   * All types accept :data:`Undefined` and convert it to
     LLVM's ``undef``.

   * All types accept ``None`` and convert it to LLVM's
     ``zeroinitializer``.

   * :class:`IntType` accepts any Python integer or boolean.

   * :class:`FloatType` and :class:`DoubleType` accept any
     Python real number.

   * Aggregate types---array and structure types---accept a
     sequence of Python values corresponding to the type's
     element types.

   * :class:`ArrayType` accepts a single :class:`bytearray`
     instance to initialize the array from a string of bytes.
     This is useful for character constants.

   .. classmethod:: literal_array(elements)

      An alternate constructor for constant arrays.

      * *elements* is a sequence of values, :class:`Constant` or
        otherwise.
      * All *elements* must have the same type.
      * Returns a constant array containing the *elements*, in
        order.

   .. classmethod:: literal_struct(elements)

      An alternate constructor for constant structs.

      * *elements* is a sequence of values, :class:`Constant` or
        otherwise. Returns a constant struct containing the
        *elements* in order.

   .. method:: bitcast(typ)

      Convert this pointer constant to a constant of the
      given pointer type.

   .. method:: gep(indices)

      Compute the address of the inner element given by the
      sequence of *indices*. The constant must have a pointer
      type.

   .. method:: inttoptr(typ)

      Convert this integer constant to a constant of the
      given pointer type.

   NOTE: You cannot define constant functions. Use a
   :ref:`function declaration` instead.

.. class:: Argument

   One of a function's arguments. Arguments have the
   :meth:`add_attribute` method.

   .. method:: add_attribute(attr)

      Add an argument attribute to this argument. *attr* is a
      Python string.

.. class:: Block

   A :ref:`basic block`.  Do not instantiate or mutate this type
   directly. Instead, call the helper methods on
   :class:`Function` and :class:`IRBuilder`.

   Basic blocks have the following methods and attributes:

   * .. method:: replace(old, new)

        Replace the instruction *old* with the other instruction
        *new* in this block's list of instructions. All uses of
        *old* in the whole function are also patched. *old* and *new*
        are :class:`Instruction` objects.

   * .. attribute:: function

        The function this block is defined in.

   * .. attribute:: is_terminated

        Whether this block ends with a
        :ref:`terminator instruction <terminator>`.

   * .. attribute:: terminator

        The block's :ref:`terminator instruction <terminator>`, if any.
        Otherwise ``None``.

.. class:: BlockAddress

   A constant representing an address of a basic block.

   Block address constants have the following attributes:

   * .. attribute:: function

        The function in which the basic block is defined.

   * .. attribute:: basic_block

        The basic block. Must be a part of :attr:`function`.


Metadata
========

There are several kinds of :ref:`metadata` values.


.. class:: MetaDataString(module, value)

   A string literal for use in metadata.

   * *module* is the module that the metadata belongs to.
   * *value* is a Python string.

.. class:: MDValue

   A metadata node. To create an instance, call
   :meth:`Module.add_metadata`.

.. class:: DIValue

   A debug information descriptor, containing key-value pairs.
   To create an instance, call :meth:`Module.add_debug_info`.

.. class:: DIToken(value)

   A debug information "token," representing a well-known
   enumeration value. *value* is the enumeration name.

   EXAMPLE: ``'DW_LANG_Python'``

.. class:: NamedMetaData

   A named metadata node. To create an instance, call
   :meth:`Module.add_named_metadata`. :class:`NamedMetaData` has
   the :meth:`add` method:

   .. method:: add(md)

      Append the given piece of metadata to the collection of
      operands referred to by the :class:`NamedMetaData`. *md* can
      be either a :class:`MetaDataString` or a :class:`MDValue`.

Global values
==============

Global values are values accessible using a module-wide name.

.. class:: GlobalValue

   The base class for global values. Global values have the
   following writable attributes:

   * .. attribute:: linkage

        A Python string describing the linkage behavior of the
        global value---for example, whether it is visible from
        other modules. The default is the empty string, meaning
        "external."

   * .. attribute:: storage_class

        A Python string describing the storage class of the
        global value.

        * The default is the empty string, meaning "default."
        * Other possible values include ``dllimport`` and
          ``dllexport``.


.. class:: GlobalVariable(module, typ, name, addrspace=0)

   A global variable.

   * *module* is where the variable is defined.

   * *typ* is the variable's type. It cannot be a function type.
     To declare a global function, use :class:`Function`.

     The type of the returned Value is a pointer to *typ*.
     To read the contents of the variable, you need to
     :meth:`~IRBuilder.load` from the returned Value.
     To write to the variable, you need to
     :meth:`~IRBuilder.store` to the returned Value.

   * *name* is the variable's name---a Python string.

   * *addrspace* is an optional address space to store the
     variable in.

   Global variables have the following writable attributes:

   * .. attribute:: global_constant

        * If ``True``, the variable is declared a constant,
          meaning that its contents cannot be modified.
        * The default is ``False``.

   * .. attribute:: unnamed_addr

        * If ``True``, the address of the variable is deemed
          insignificant, meaning that it is merged with other
          variables that have the same initializer.
        * The default is ``False``.

   * .. attribute:: initializer

        The variable's initialization value---probably a
        :class:`Constant` of type *typ*. The default is ``None``,
        meaning that the variable is uninitialized.

   * .. attribute:: align

        An explicit alignment in bytes. The default is ``None``,
        meaning that the default alignment for the variable's
        type is used.

.. class:: Function(module, typ, name, arg_names=None)

   A global function.

   * *module* is where the function is defined.
   * *typ* is the function's type---a :class:`FunctionType`
     instance.
   * *name* is the function's name---a Python string.
   * *arg_names* is an optional sequence of Python strings
     with the names for the function's arguments.

   If a global function has any basic blocks, it is a
   :ref:`function definition`. Otherwise, it is a
   :ref:`function declaration`.

   Functions have the following methods and attributes:

   * .. method:: append_basic_block(name='')

        Append a :ref:`basic block` to this function's body.

        * If *name* is not empty, it names the block's entry
          :ref:`label`.
        * Returns a new :class:`Block`.

   * .. method:: insert_basic_block(before, name='')

        Similar to :meth:`append_basic_block`, but inserts it
        before the basic block *before* in the function's list
        of basic blocks.

   * .. method:: set_metadata(name, node)

        Add a function-specific metadata named *name* pointing to the
        given metadata *node*---an :class:`MDValue`.

   * .. attribute:: args

        The function's arguments as a tuple of :class:`Argument`
        instances.

   * .. attribute:: attributes

        A set of function attributes. Each optional attribute is
        a Python string. By default this is empty. Use the
        `.add()` method to add an attribute::

         fnty = ir.FunctionType(ir.DoubleType(), (ir.DoubleType(),))
         fn = Function(module, fnty, "sqrt")
         fn.attributes.add("alwaysinline")

   * .. attribute:: calling_convention

        The function's calling convention---a Python string. The
        default is the empty string.

   * .. attribute:: is_declaration

        Indicates whether the global function is a declaration
        or a definition.

        * If ``True``, it is a declaration.
        * If ``False``, it is a definition.


Instructions
=============

Every :ref:`instruction` is also a value:

* It has a name---the recipient's name.
* It has a well-defined type.
* It can be used as an operand in other instructions or in
  literals.

Usually, you should not instantiate instruction types directly.
Use the helper methods on the :class:`IRBuilder` class.

.. class:: Instruction

   The base class for all instructions. Instructions have the
   following method and attributes:

   * .. method:: set_metadata(name, node)

        Add an instruction-specific metadata *name* pointing to the
        given metadata *node*---an :class:`MDValue`.

   * .. method:: replace_usage(old, new)

        Replace the operand *old* with the other instruction *new*.

   * .. attribute:: function

        The function that contains this instruction.

   * .. attribute:: module

        The module that defines this instruction's function.


.. class:: PredictableInstr

   The class of instructions for which we can specify the
   probabilities of different outcomes---for example, a switch or
   a conditional branch. Predictable instructions have the
   :meth:`set_weights` method.

   .. method:: set_weights(weights)

      Set the weights of the instruction's possible outcomes.
      *weights* is a sequence of positive integers, each
      corresponding to a different outcome and specifying its
      relative probability compared to other outcomes. The
      greater the number, the likelier the outcome.


.. class:: SwitchInstr

   A switch instruction. Switch instructions have the
   :meth:`add_case` method.

   .. method:: add_case(val, block)

      Add a case to the switch instruction.

      * *val* should be a :class:`Constant` or a Python value
        compatible with the switch instruction's operand type.
      * *block* is a :class:`Block` to jump to if val and the
        switch operand compare equal.

.. class:: IndirectBranch

   An indirect branch instruction. Indirect branch instructions
   have the :meth:`add_destination` method.

   .. method:: add_destination(value, block)

      Add an outgoing edge. The indirect branch instruction must
      refer to every basic block it can transfer control to.

.. class:: PhiInstr

   A phi instruction. Phi instructions have the
   :meth:`add_incoming` method.

   .. method:: add_incoming(value, block)

      Add an incoming edge. Whenever transfer is controlled
      from *block*---a :class:`Block`---the phi instruction
      takes the given *value*.

.. class:: LandingPad

   A landing pad. Landing pads have the :meth:`add_clause` method:

   .. method:: add_clause(value, block)

      Add a catch or filter clause. Create catch clauses using
      :class:`CatchClause` and filter clauses using
      :class:`FilterClause`.


Landing pad clauses
====================

Landing pads have the following classes associated with them.

.. class:: CatchClause(value)

   A catch clause. Instructs the personality function to compare
   the in-flight exception typeinfo with *value*, which should
   have type `IntType(8).as_pointer().as_pointer()`.

.. class:: FilterClause(value)

   A filter clause. Instructs the personality function to check
   inclusion of the the in-flight exception typeinfo in *value*,
   which should have type
   `ArrayType(IntType(8).as_pointer().as_pointer(), ...)`.
