
Example
=======

.. _ir-fpadd:

A trivial function
------------------

Define a function adding two double-precision floating-point numbers.

.. literalinclude:: /../../examples/ir_fpadd.py

The generated LLVM :term:`IR` is printed out at the end, and should look
like this:

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

To learn how to compile and execute this function, refer to the
:ref:`binding layer <binding-layer>` documentation.
