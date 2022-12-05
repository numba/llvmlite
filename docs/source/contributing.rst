
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
<https://numba.discourse.group/c/llvmlite/12>`_.

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
* All C++ code is formatted using ``clang-format-13`` from the
  ``clang-format-13`` package available in the ``conda-forge`` conda channel.
* Code and documentation should generally fit within 80 columns,
  for maximum readability with all existing tools, such as code
  review user interfaces.

Optionally, you may wish to setup `pre-commit hooks <https://pre-commit.com/>`_
to automatically run ``clang-format`` when you make a git commit. This can be
done by installing ``pre-commit``::

    pip install pre-commit

and then running::

    pre-commit install

from the root of the Numba repository. Now ``clang-format`` will be run each time
you commit changes. You can skip this check with ``git commit --no-verify``.


Platform support
----------------

Llvmlite will be kept compatible with Python 3.8 and later
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
