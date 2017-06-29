====================================
Example---defining a simple function
====================================

.. _ir-fpadd:

This example defines a function that adds 2 double-precision, 
floating-point numbers.

.. literalinclude:: ../examples/ir_fpadd.py

The generated LLVM 
:ref:`intermediate representation <intermediate representation>` 
is printed at the end:

.. code-block:: llvm

   ; ModuleID = "examples/ir_fpadd.py"
   target triple = "unknown-unknown-unknown"
   target datalayout = ""

   define double @"fpadd"(double %".1", double %".2")
   {
   entry:
     %"res" = fadd double %".1", %".2"
     ret double %"res"
   }

To learn how to compile and execute this function, see 
:doc:`../binding/index`.