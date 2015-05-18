
.. _ir-values:

Values
======

.. currentmodule:: llvmlite.ir

Values are what a :term:`module` mostly consists of.


.. data:: Undefined

   An undefined value (mapping to LLVM's "undef").


.. class:: Constant(typ, constant)

   A literal value.  *typ* is the type of the represented value
   (a :class:`~llvmlite.ir.Type` instance).  *constant* is the Python
   value to be represented.  Which Python types are allowed for *constant*
   depends on *typ*:

   * All types accept :data:`Undefined`, and turn it into LLVM's "undef".

   * All types accept None, and turn it into LLVM's "zeroinitializer".

   * :class:`IntType` accepts any Python integer or boolean.

   * :class:`FloatType` and :class:`DoubleType` accept any Python real number.

   * Aggregate types (i.e. array and structure types) accept a sequence of
     Python values corresponding to the type's element types.

   * In addition, :class:`ArrayType` also accepts a single :class:`bytearray`
     instance to initialize the array from a string of bytes.  This is
     useful for character constants.

   .. classmethod:: literal_struct(elements)

      An alternate constructor for constant structs.  *elements* is a
      sequence of values (:class:`Constant` or otherwise).  A constant
      struct containing the *elems* in order is returned

   .. note::
      You cannot define constant functions.  Use a :term:`function declaration`
      instead.


.. class:: Value

   The base class for non-literal values.


.. class:: MetaDataString(module, value)

   A string literal for use in :term:`metadata`.  *module* is the module
   the metadata belongs to.  *value* is a Python string.

.. class:: MDValue

   A :term:`metadata` node.  To create an instance, call
   :meth:`Module.add_metadata`.

.. class:: NamedMetaData

   A named metadata.  To create an instance, call
   :meth:`Module.add_named_metadata`.  Named metadata has
   the following method:

   .. method:: add(md)

      Append the given piece of metadata to the collection of operands
      referred to by the NamedMetaData.  *md* can be either a
      :class:`MetaDataString` or a :class:`MDValue`.


.. class:: Argument

   One of a function's arguments.  Arguments have the following method:

   .. method:: add_attribute(attr)

      Add an argument attribute to this argument.  *attr* is a Python string.


.. class:: Block

   A :term:`basic block`.  You shouldn't instantiate or mutate this type
   directly;  instead, call the helper methods on :class:`Function`
   and :class:`IRBuilder`.

   Basic blocks have the following methods and attributes:

   .. method:: replace(old, new)

      Replace the instruction *old* with the other instruction *new*
      in this block's list of instructions.  All uses of *old* in the whole
      function are also patched.  *old* and *new* are :class:`Instruction`
      objects.

   .. attribute:: function

      The function this block is defined in.

   .. attribute:: is_terminated

      Whether this block ends with a :term:`terminator instruction`.

   .. attribute:: terminator

      The block's :term:`terminator instruction`, if any.  Otherwise None.


Global values
-------------

Global values are values accessible using a module-wide name.

.. class:: GlobalValue

   The base class for global values.  Global values have the following
   writable attribute:

   .. attribute:: linkage

      A Python string describing the linkage behaviour of the global value
      (e.g. whether it is visible from other modules).  Default is the
      empty string, meaning "external".


.. class:: GlobalVariable(module, typ, name, addrspace=0)

   A global variable.  *module* is where the variable will be defined.
   *typ* is the variable's type.  *name* is the variable's name
   (a Python string).  *addrspace* is an optional address space to
   store the variable in.

   *typ* cannot be a function type.  To declare a global function,
   use :class:`Function`.

   The returned Value's actual type is a pointer to *typ*. To read
   (respectively write) the variable's contents, you need to
   :meth:`~IRBuilder.load` from (respectively :meth:`~IRBuilder.store` to)
   the returned Value.

   Global variables have the following writable attributes:

   .. attribute:: global_constant

      If true, the variable is declared a constant, i.e. its contents
      cannot be ever modified.  Default is False.

   .. attribute:: initializer

      The variable's initialization value (probably a :class:`Constant`
      of type *typ*).  Default is None, meaning the variable is uninitialized.


.. class:: Function(module, typ, name)

   A global function.  *module* is where the function will be defined.
   *typ* is the function's type (a :class:`FunctionType` instance).
   *name* is the function's name (a Python string).

   If a global function has any basic blocks, it is a :term:`function definition`.
   Otherwise, it is a :term:`function declaration`.

   Functions have the following methods and attributes:

   .. method:: append_basic_block(name='')

      Append a :term:`basic block` to this function's body.  If *name* is
      non empty, it names the block's entry :term:`label`.

      A new :class:`Block` is returned.

   .. method:: insert_basic_block(before, name='')

      Similar to :meth:`append_basic_block`, but inserts it before the basic
      block *before* in the function's list of basic blocks.

   .. attribute:: args

      The function's arguments as a tuple of :class:`Argument` instances.

   .. attribute:: attributes

      A set of function attributes.  Each optional attribute is a Python
      string.  By default this is empty.  Use the ``add()`` method to
      add an attribute::

         fnty = ir.FunctionType(ir.DoubleType(), (ir.DoubleType(),))
         fn = Function(module, fnty, "sqrt")
         fn.attributes.add("alwaysinline")

   .. attribute:: calling_convention

      The function's calling convention (a Python string).  Default is
      the empty string.

   .. attribute:: is_declaration

      Whether the global function is a declaration (True) or a definition
      (False).


Instructions
------------

Every :term:`instruction` is also a value: it has a name (the recipient's
name), a well-defined type, and can be used as an operand in other
instructions or in literals.

Instruction types should usually not be instantiated directly.  Instead,
use the helper methods on the :class:`IRBuilder` class.

.. class:: Instruction

   The base class for all instructions.  Instructions have the following
   method and attributes:

   .. method:: set_metadata(name, node)

      Add an instruction-specific metadata named *name* pointing to the
      given metadata *node* (a :class:`MDValue`).

   .. attribute:: function

      The function this instruction is part of.

   .. attribute:: module

      The module this instruction's function is defined in.


.. class:: PredictableInstr

   The class of instructions for which we can specificy the probabilities
   of different outcomes (e.g. a switch or a conditional branch).  Predictable
   instructions have the following method:

   .. method:: set_weights(weights)

      Set the weights of the instruction's possible outcomes.
      *weights* is a sequence of positive integers, each corresponding
      to a different outcome and specifying its relative probability
      compared to other outcomes (the greater, the likelier).


.. class:: SwitchInstr

   A switch statement.  Switch statements have the following method:

   .. method:: add_case(val, block)

      Add a case to the switch statements.  *val* should be a :class:`Constant`
      or a Python value compatible with the switch statement's operand type.
      *block* is a :class:`Block` to jump to if, and only if, *val* and
      the switch operand compare equal.


.. class:: PhiInstr

   A phi instruction.  Phi instructions have the following method:

   .. method:: add_incoming(value, block)

      Add an incoming edge.  Whenever transfer is controlled from *block*
      (a :class:`Block`), the phi instruction takes the given *value*.

