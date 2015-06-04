
Glossary
========

.. glossary::

   basic block
      A sequence of instructions inside a function.  A basic block always
      starts with a :term:`label` and ends with a :term:`terminator`.
      No other instruction inside the basic block can transfer control out
      of the block.

   function declaration
      The specification of a function's prototype (including the argument
      and return types, and other information such as the calling
      convention), without an associated implementation.  This is like
      a ``extern`` function declaration in C.

   function definition
      A function's prototype (like in a :term:`function declaration`)
      plus a body implementing the function.

   getelementptr
      A LLVM :term:`instruction` allowing to get the address of a subelement
      of an aggregate data structure.

      .. seealso::
         Official documentation: :llvm:ref:`i_getelementptr`

   global value
      A named value accessible to all members of a module.

   global variable
      A variable whose value is accessible to all members of a module.
      Under the hood, it is a constant pointer to a module-allocated
      slot of the given type.

      All global variables are global values.  However, the converse is
      not true: a function declaration or definition is not a global
      variable; it is only a :term:`global value`.

   instruction
      The fundamental element(s) used in implementing a LLVM function.
      LLVM instructions define a procedural assembly-like language.

   IR
   Intermediate Representation
      A high-level assembly language describing to LLVM the code to be
      compiled to native code.

   label
      A branch target inside a function.  A label always denotes the start
      of a :term:`basic block`.

   metadata
      Optional ancillary information which can be associated with LLVM
      instructions, functions, etc.  Metadata is used to convey certain
      information which is not critical to the compiling of LLVM :term:`IR`
      (such as the likelihood of a condition branch or the source code
      location corresponding to a given instruction).

   module
      A compilation unit for LLVM :term:`IR`.  A module can contain any
      number of function declarations and definitions, global variables,
      and metadata.

   terminator
   terminator instruction
      A kind of :term:`instruction` which explicitly transfers control
      to another part of the program (instead of simply going to the next
      instruction after it is executed).  Examples are branches and
      function returns.
