===========
Object file
===========

.. currentmodule:: llvmlite.binding

The object file is an abstraction of LLVM representation of
the static object code files. This class provides methods to examine
the contents of the object files. It also can be passed as parameter to
:meth:`ExecutionEngine.add_object_file` to make the symbols available
to the JIT.

The ObjectFileRef class
------------------------

.. class:: ObjectFileRef

    A wrapper around LLVM object file. The following methods and properties
    are available:

    * .. classmethod:: from_data(data):

        Create an instance of ObjectFileRef from the provided binary data.

    * .. classmethod:: from_path(path):

        Create an instance of ObjectFileRef from the supplied filesystem
        path. Raises IOError if the path does not exist.

    * .. method:: sections:

        Return an iterator to the sections objects consisting of the
        instance of :class:`SectionIteratorRef`

The SectionIteratorRef class
----------------------------

.. class:: SectionIteratorRef
    A wrapper around the section class which provides information like
    section name, type and size, etc.

    * .. method:: name():

        Get section name.

    * .. method:: is_text():

        Returns true when section is of type text.

    * .. method:: size():

        Get section size.

    * .. method:: address():

        Get section address.

    * .. method:: data():

        Get section contents.

    * .. method:: is_end(object_file):

        Return true if the section iterator is the last element of the
        object_file.

        * object_file: an instance of :class:`ObjectFileRef`

    * .. method:: next():

        Get the next section instance.

