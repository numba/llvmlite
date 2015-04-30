
IR builders
===========

.. currentmodule:: llvmlite.ir

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

   Create a new IR builder.  If *block* (a :class:`BasicBlock`) is given,
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
   :class:`BasicBlock` is returned.


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

