
========
Glossary
========

.. contents::
   :local:
   :depth: 1


.. _basic block:

Basic block
===========

A sequence of instructions inside a function. A basic block
always starts with a :ref:`label` and ends with a
:ref:`terminator <terminator>`. No other instruction inside the
basic block can transfer control out of the block.

.. _function declaration:

Function declaration
====================

The specification of a function's prototype without an
associated implementation. A declaration includes the argument
types, return types and other information such as the calling
convention. This is like an ``extern`` function declaration in C.

.. _function definition:

Function definition
===================

A function's prototype, as in a :ref:`function declaration`,
plus a body implementing the function.

.. _getelementptr:

getelementptr
=============

An LLVM :ref:`instruction` that lets you get the address of a
subelement of an aggregate data structure.

See `the getelementptr instruction
<https://releases.llvm.org/10.0.0/docs/LangRef.html#i-getelementptr>`_ in the
official LLVM documentation.


.. _global value:

Global value
============

A named value accessible to all members of a module.

.. _global variable:

Global variable
===============

A variable whose value is accessible to all members of a module.
It is a constant pointer to a module-allocated slot of the given
type.

All global variables are global values.  However, the opposite is
not true---function declarations and function definitions are not
global variables, they are only :ref:`global values <global value>`.

.. _instruction:

Instruction
===========

The fundamental element used in implementing an LLVM function.
LLVM instructions define a procedural, assembly-like language.

.. _IR:

.. _intermediate representation:

Intermediate representation (IR)
================================

High-level assembly-language code describing to LLVM the
program to be compiled to native code.

.. _label:

Label
=====

A branch target inside a function. A label always denotes the
start of a :ref:`basic block`.

.. _metadata:

Metadata
========

Optional information associated with LLVM instructions,
functions and other code. Metadata provides information that is
not critical to the compiling of an
LLVM :ref:`intermediate representation <IR>`, such as the
likelihood of a condition branch or the source code location
corresponding to a given instruction.

.. _module:

Module
======

A compilation unit for LLVM :ref:`intermediate representation <IR>`.
A module can contain any number of function declarations and
definitions, global variables and metadata.

.. _terminator:

.. _terminator instruction:

Terminator, terminator instruction
==================================

A kind of :ref:`instruction` that explicitly transfers control
to another part of the program instead of going to the next
instruction after it is executed. Examples are branches and
function returns.
