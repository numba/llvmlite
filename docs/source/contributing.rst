
========================
Contributing to llvmlite
========================

llvmlite originated to fulfill the needs of the Numba_ project.
It is maintained mostly by the Numba team. We tend to prioritize
the needs and constraints of Numba over other conflicting desires.

We do welcome any contributions in the form of
:ref:`bug reports <report-bugs>` or :ref:`pull requests <pull-requests>`.

.. _Numba: http://numba.pydata.org/

.. contents::
   :local:
   :depth: 1

Communication methods
=====================

Forum
-----

llvmlite uses the Numba Discourse as a forum for longer running threads such as
design discussions and roadmap planning. There are various categories available
and it can be reached at: `numba.discourse.group
<https://numba.discourse.group/>`_. It also has a `llvmlite topic
<https://numba.discourse.group/c/llvmlite/12>`.

.. _report-bugs:

Bug reports
-----------

We use the
`Github issue tracker <https://github.com/numba/llvmlite/issues>`_
to track both bug reports and feature requests. If you report an
issue, please include:

* What you are trying to do.

* Your operating system.

* What version of llvmlite you are running.

* A description of the problem---for example, the full error
  traceback or the unexpected results you are getting.

* As far as possible, a code snippet that allows full
  reproduction of your problem.

.. _pull-requests:

Pull requests
-------------

To contribute code:

#. Fork our `Github repository <https://github.com/numba/llvmlite>`_.

#. Create a branch representing your work.

#. When your work is ready, submit it as a pull request from the
   Github interface.


Development rules
=================

Coding conventions
------------------

* All Python code should follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.
* Our C++ code does not have a well-defined coding style.
* Code and documentation should generally fit within 80 columns,
  for maximum readability with all existing tools, such as code
  review user interfaces.


Platform support
----------------

Llvmlite will be kept compatible with Python 3.7 and later
under at least Windows, macOS and Linux.

We do not expect contributors to test their code on all platforms.  Pull
requests are automatically built and tested using `Azure Pipelines
<https://dev.azure.com/numba/numba/_build?definitionId=2>`_ for Winows, OSX and
Linux.

Documentation
=============

This llvmlite documentation is built using Sphinx and maintained
in the ``docs`` directory inside the
`llvmlite repository <https://github.com/numba/llvmlite>`_.

#. Edit the source files under ``docs/source/``.

#. Build the documentation::

     make html

#. Check the documentation::

     open _build/html/index.html

.. |reg| unicode:: U+000AE .. REGISTERED SIGN
