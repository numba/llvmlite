
Contributing
============

llvmlite originated to fulfill the needs of the Numba_ project.  It is
still mostly maintained by the Numba_ team.  As such, we tend to prioritize
the needs and constraints of Numba_ over other conflicting desires.
However, we welcome any contributions, under the form of
:ref:`bug reports <report-bugs>` or :ref:`pull requests <pull-requests>`.

.. _Numba: http://numba.pydata.org/


Communication
-------------

Mailing-list
''''''''''''

For now, we use the Numba_ public mailing-list, which you can e-mail at
numba-users@continuum.io.  If you have any questions about contributing to
llvmlite, it is ok to ask them on this mailing-list.  You can subscribe
and read the archives on
`Google Groups <https://groups.google.com/a/continuum.io/forum/#!forum/numba-users>`_,
and there is also a `Gmane mirror <http://news.gmane.org/gmane.comp.python.numba.user>`_
allowing NNTP access.

.. _report-bugs:

Bug tracker
''''''''''''

We use the `Github issue tracker <https://github.com/numba/llvmlite/issues>`_
to track both bug reports and feature requests.  If you report an issue,
please include specifics:

* what you are trying to do;
* which operating system you have and which version of llvmlite you are running;
* how llvmlite is misbehaving, e.g. the full error traceback, or the unexpected
  results you are getting;
* as far as possible, a code snippet that allows full reproduction of your
  problem.


.. _pull-requests:

Pull requests
-------------

If you want to contribute code, we recommend you fork our `Github repository
<https://github.com/numba/llvmlite>`_, then create a branch representing
your work.  When your work is ready, you should submit it as a pull
request from the Github interface.


Development rules
-----------------

Coding conventions
''''''''''''''''''

All Python code should follow :pep:`8`.  Our C++ code doesn't have a
well-defined coding style (would it be nice to follow :pep:`7`?).
Code and documentation should generally fit within 80 columns, for
maximum readability with all existing tools (such as code review UIs).

Platform support
''''''''''''''''

llvmlite is to be kept compatible with Python 2.7, 3.4 and later under
at least Linux, OS X and Windows.  It only needs to be compatible with
the currently supported LLVM version (currently, the 3.8 series).

We don't expect contributors to test their code on all platforms.  Pull
requests are automatically built and tested using
`Travis-CI <https://travis-ci.org/numba/llvmlite>`_.  This takes care of
Linux compatibility.  Other operating systems are tested on an internal
continuous integration platform at Continuum Analytics.


Documentation
-------------

This documentation is maintained in the ``docs`` directory inside the
`llvmlite repository <https://github.com/numba/llvmlite>`_.  It is
built using Sphinx.

You can edit the source files under ``docs/source/``, after which you can
build and check the documentation::

   $ make html
   $ open _build/html/index.html

