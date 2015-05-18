
Modules
=======

.. currentmodule:: llvmlite.ir

A module is a compilation unit.  It defines a set of related functions,
global variables and metadata.  In the IR layer, a module is representated
by the :class:`Module` class.


.. class:: Module(name='')

   Create a module.  The optional *name*, a Python string, can be specified
   for informational purposes.

   Modules have the following methods and attributes:

   .. method:: add_global(globalvalue)

      Add the given *globalvalue* (a :class:`GlobalValue`) to this module.
      It should have a unique name in the whole module.

   .. method:: add_metadata(operands)

      Add an unnamed :term:`metadata` node to the module with the given
      *operands* (a list of metadata-compatible values).  If another
      metadata node with equal operands already exists in the module, it
      is reused instead.  A :class:`MDValue` is returned.

   .. method:: add_named_metadata(name)

      Add a named metadata with the given *name*.  A :class:`NamedMetaData`
      is returned.

   .. method:: get_global(name)

      Get the :term:`global value` (a :class:`GlobalValue`) with the given
      *name*.  :exc:`KeyError` is raised if it doesn't exist.

   .. method:: get_named_metadata(name)

      Return the named metadata with the given *name*.  :exc:`KeyError`
      is raised if it doesn't exist.

   .. method:: get_unique_name(name)

      Return a unique name accross the whole module.  *name* is the
      desired name, but a variation can be returned if it is already in use.

   .. attribute:: data_layout

      A string representing the data layout in LLVM format.

   .. attribute:: functions

      The list of functions (as :class:`Function` instances) declared or
      defined in the module.

   .. attribute:: global_values

      An iterable of global values in this module.

   .. attribute:: triple

      A string representing the target architecture in LLVM "triple" form.

