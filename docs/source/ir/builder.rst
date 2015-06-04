
IR builders
===========

.. currentmodule:: llvmlite.ir

.. sidebar:: Contents

   .. contents::
      :depth: 2
      :local:

:class:`IRBuilder` is the workhorse of LLVM :term:`IR` generation.  It allows
you to fill the :term:`basic blocks <basic block>` of your functions with
LLVM instructions.

A :class:`IRBuilder` internally maintains a current basic block, and a
pointer inside the block's list of instructions.  When adding a new
instruction, it is inserted at that point and the pointer is then advanced
after the new instruction.

Instantiation
-------------

.. class:: IRBuilder(block=None)

   Create a new IR builder.  If *block* (a :class:`Block`) is given,
   the builder starts right at the end of this basic block.


Properties
----------

:class:`IRBuilder` has the following attributes:

.. attribute:: IRBuilder.block

   The basic block the builder is operating on.

.. attribute:: IRBuilder.function

   The function the builder is operating on.

.. attribute:: IRBuilder.module

   The module the builder's function is defined in.


Utilities
---------

.. method:: IRBuilder.append_basic_block(name='')

   Append a basic block, with the given optional *name*, to the current
   function.  The current block is not changed.  A
   :class:`Block` is returned.


Positioning
-----------

The following :class:`IRBuilder` methods help you move the current
instruction pointer around:

.. method:: IRBuilder.position_before(instruction)

   Position immediatly before the given *instruction*.  The current block
   is also changed to the instruction's basic block.

.. method:: IRBuilder.position_after(instruction)

   Position immediatly after the given *instruction*.  The current block
   is also changed to the instruction's basic block.

.. method:: IRBuilder.position_at_start(block)

   Position at the start of the basic *block*.

.. method:: IRBuilder.position_at_end(block)

   Position at the end of the basic *block*.


The following context managers allow you to temporarily switch to another
basic block, then go back where you were:

.. method:: IRBuilder.goto_block(block)

   A context manager which positions the builder either at the end of the
   basic *block*, if it is not terminated, or just before the *block*'s
   terminator::

      new_block = builder.append_basic_block('foo')
      with builder.goto_block(new_block):
         # Now the builder is at the end of *new_block*
         # ... add instructions

      # Now the builder has returned to its previous position


.. method:: IRBuilder.goto_entry_block()

   Just like :meth:`goto_block`, but with the current function's entry
   block.


Flow control helpers
--------------------

The following context managers make it easier to create conditional code.

.. method:: IRBuilder.if_then(pred, likely=None)

   A context manager which creates a basic block whose execution is
   conditioned on predicate *pred* (a value of type ``IntType(1)``).
   Another basic block is created for instructions after the conditional
   block.  The current basic block is terminated with a conditional branch
   based on *pred*.

   When the context manager is entered, the builder positions at the
   end of the conditional block.  When the context manager is exited,
   the builder positions at the start of the continuation block.

   If *likely* is not None, it indicates whether *pred* is likely to be
   true, and metadata is emitted to specify branch weights in accordance.


.. method:: IRBuilder.if_else(pred, likely=None)

   A context manager which sets up two basic blocks whose execution
   is condition on predicate *pred* (a value of type ``IntType(1)``).
   *likely* has the same meaning as in if_then().

   A pair of context managers is yield'ed.  Each of them acts as a
   :meth:`if_then()` context manager: the first one for the block
   to be executed if *pred* is true, the second one for the block
   to be executed if *pred* is false.

   When the context manager is exited, the builder is positioned on
   a new continuation block which both conditional blocks jump into.

   Typical use:

   .. code-block:: Python

      with builder.if_else(pred) as (then, otherwise):
          with then:
              # emit instructions for when the predicate is true
          with otherwise:
              # emit instructions for when the predicate is false
      # emit instructions following the if-else block


Instruction building
--------------------

The following methods all insert a new instruction (a
:class:`Instruction` instance) at the current index in the current block.
The new instruction is returned.

An instruction's operands are most always :ref:`values <ir-values>`.

Many of these methods also take an optional *name* argument, specifying the
local *name* of the result value.  If not given, a unique name is
automatically generated.

Arithmetic
''''''''''

.. method:: IRBuilder.shl(lhs, rhs, name='')

   Left-shift *lhs* by *rhs* bits.

.. method:: IRBuilder.lshr(lhs, rhs, name='')

   Logical right-shift *lhs* by *rhs* bits.

.. method:: IRBuilder.ashr(lhs, rhs, name='')

   Arithmetic (signed) right-shift *lhs* by *rhs* bits.

.. method:: IRBuilder.add(lhs, rhs, name='')

   Integer add *lhs* and *rhs*.

.. method:: IRBuilder.fadd(lhs, rhs, name='')

   Floating-point add *lhs* and *rhs*.

.. method:: IRBuilder.sub(lhs, rhs, name='')

   Integer subtract*rhs* from *lhs*.

.. method:: IRBuilder.fadd(lhs, rhs, name='')

   Floating-point subtract *rhs* from *lhs*.

.. method:: IRBuilder.mul(lhs, rhs, name='')

   Integer multiply *lhs* with *rhs*.

.. method:: IRBuilder.fmul(lhs, rhs, name='')

   Floating-point multiply *lhs* with *rhs*.

.. method:: IRBuilder.sdiv(lhs, rhs, name='')

   Signed integer divide *lhs* by *rhs*.

.. method:: IRBuilder.udiv(lhs, rhs, name='')

   Unsigned integer divide *lhs* by *rhs*.

.. method:: IRBuilder.fdiv(lhs, rhs, name='')

   Floating-point divide *lhs* by *rhs*.

.. method:: IRBuilder.srem(lhs, rhs, name='')

   Signed integer remainder of *lhs* divided by *rhs*.

.. method:: IRBuilder.urem(lhs, rhs, name='')

   Unsigned integer remainder of *lhs* divided by *rhs*.

.. method:: IRBuilder.frem(lhs, rhs, name='')

   Floating-point remainder of *lhs* divided by *rhs*.

.. method:: IRBuilder.and_(lhs, rhs, name='')

   Bitwise AND *lhs* with *rhs*.

.. method:: IRBuilder.or_(lhs, rhs, name='')

   Bitwise OR *lhs* with *rhs*.

.. method:: IRBuilder.xor(lhs, rhs, name='')

   Bitwise XOR *lhs* with *rhs*.

.. method:: IRBuilder.not_(value, name='')

   Bitwise complement *value*.

.. method:: IRBuilder.neg(value, name='')

   Negate *value*.

Conversions
'''''''''''

.. method:: IRBuilder.trunc(value, typ, name='')

   Truncate integer *value* to integer type *typ*.

.. method:: IRBuilder.zext(value, typ, name='')

   Zero-extend integer *value* to integer type *typ*.

.. method:: IRBuilder.sext(value, typ, name='')

   Sign-extend integer *value* to integer type *typ*.

.. method:: IRBuilder.fptrunc(value, typ, name='')

   Truncate (approximate) floating-point *value* to floating-point type *typ*.

.. method:: IRBuilder.fpext(value, typ, name='')

   Extend floating-point *value* to floating-point type *typ*.

.. method:: IRBuilder.fptosi(value, typ, name='')

   Convert floating-point *value* to signed integer type *typ*.

.. method:: IRBuilder.fptoui(value, typ, name='')

   Convert floating-point *value* to unsigned integer type *typ*.

.. method:: IRBuilder.sitofp(value, typ, name='')

   Convert signed integer *value* to floating-point type *typ*.

.. method:: IRBuilder.uitofp(value, typ, name='')

   Convert unsigned integer *value* to floating-point type *typ*.

.. method:: IRBuilder.ptrtoint(value, typ, name='')

   Convert pointer *value* to integer type *typ*.

.. method:: IRBuilder.inttoptr(value, typ, name='')

   Convert integer *value* to pointer type *typ*.

.. method:: IRBuilder.bitcast(value, typ, name='')

   Convert pointer *value* to pointer type *typ*.

.. method:: IRBuilder.addrspacecast(value, typ, name='')

   Convert pointer *value* to pointer type *typ* of different address space.


Comparisons
'''''''''''

.. method:: IRBuilder.icmp_signed(cmpop, lhs, rhs, name='')

   Signed integer compare *lhs* with *rhs*.  *cmpop*, a string, can be one
   of ``<``, ``<=``, ``==``, ``!=``, ``>=``, ``>``.

.. method:: IRBuilder.icmp_unsigned(cmpop, lhs, rhs, name='')

   Unsigned integer compare *lhs* with *rhs*.  *cmpop*, a string, can be one
   of ``<``, ``<=``, ``==``, ``!=``, ``>=``, ``>``.

.. method:: IRBuilder.fcmp_ordered(cmpop, lhs, rhs, name='')

   Floating-point ordered compare *lhs* with *rhs*.  *cmpop*, a string, can
   be one of ``<``, ``<=``, ``==``, ``!=``, ``>=``, ``>``, ``ord``, ``uno``.

.. method:: IRBuilder.fcmp_unordered(cmpop, lhs, rhs, name='')

   Floating-point unordered compare *lhs* with *rhs*.  *cmpop*, a string, can
   be one of ``<``, ``<=``, ``==``, ``!=``, ``>=``, ``>``, ``ord``, ``uno``.


Conditional move
''''''''''''''''

.. method:: IRBuilder.select(cond, lhs, rhs, name='')

   Two-way select: *lhs* if *cond* else *rhs*.


Phi
'''

.. method:: IRBuilder.phi(typ, name='')

   Create a phi node.  Add incoming edges and their values using
   the :meth:`~PhiInstr.add_incoming` method on the return value.


Aggregate operations
''''''''''''''''''''

.. method:: IRBuilder.extract_value(agg, index, name='')

   Extract the element at *index* of the
   :ref:`aggregate value <aggregate-types>` *agg*.
   *index* may be an integer or a sequence of integers.  If *agg* is of an
   array type, indices can be arbitrary values; if *agg* is of a struct
   type, indices have to be constant.

.. method:: IRBuilder.insert_value(agg, value, index, name='')

   Build a copy of :ref:`aggregate value <aggregate-types>` *agg* by setting
   the new *value* at *index*.  *index* can be of the same types as in
   :meth:`extract_value`.


Memory
''''''

.. method:: IRBuilder.alloca(typ, size=None, name='')

   Statically allocate a stack slot for *size* values of type *typ*.
   If *size* is not given, a stack slot for one value is allocated.

.. method:: IRBuilder.load(ptr, name='')

   Load value from pointer *ptr*.

.. method:: IRBuilder.store(value, ptr)

   Store *value* to pointer *ptr*.

.. method:: IRBuilder.gep(ptr, indices, inbounds=False, name='')

   The :term:`getelementptr` instruction.  Given a pointer *ptr* to an
   aggregate value, compute the address of the inner element given by
   the sequence of *indices*.

.. method:: cmpxchg(ptr, cmp, val, ordering, failordering=None, name='')

   Atomic compare-and-swap at address *ptr*.  *cmp* is the value to compare
   the contents with, *val* the new value to be swapped into.
   Optional *ordering* and *failordering* specify the memory model for
   this instruction.

.. method:: atomic_rmw(op, ptr, val, ordering, name='')

   Atomic in-memory operation *op* at address *ptr*, with operand *val*.
   *op* is a string specifying the operation (e.g. ``add`` or ``sub``).
   The optional *ordering* specifies the memory model for this instruction.


Function call
'''''''''''''

.. method:: IRBuilder.call(fn, args, name='', cconv=None, tail=False)

   Call function *fn* with arguments *args* (a sequence of values).
   *cconc* is the optional calling convention.  *tail*, if true, is
   a hint for the optimizer to perform tail-call optimization.


Branches
''''''''

These instructions are all :term:`terminators <terminator>`.

.. method:: IRBuilder.branch(target)

   Unconditional jump to the *target* (a :class:`Block`).

.. method:: IRBuilder.cbranch(cond, truebr, falsebr)

   Conditional jump to either *truebr* or *falsebr* (both :class:`Block`
   instances), depending on *cond*.  This instruction is a
   :class:`PredictableInstr`.

.. method:: IRBuilder.ret(value)

   Return the *value* from the current function.

.. method:: IRBuilder.ret_void()

   Return from the current function without a value.

.. method:: IRBuilder.switch(value, default)

   Switch to different blocks based on the *value*.  *default* is the
   block to switch to if no other block is matched.

   Add non-default targets using the :meth:`~SwitchInstr.add_case`
   method on the return value.


Miscellaneous
'''''''''''''

.. method:: IRBuilder.unreachable()

   Mark an unreachable point in the code.
