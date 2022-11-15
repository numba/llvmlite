"""
Tests for setup.py behavior
"""

import distutils.core
try:
    import setuptools
except ImportError:
    setuptools = None
import sys
import unittest
from collections import namedtuple
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

from . import TestCase

setup_path = Path(__file__).parent.parent.parent / "setup.py"


class TestSetup(TestCase):

    @unittest.skipUnless(setup_path.is_file(), 'Need setup.py from source tree')
    def test_guard_py_ver(self):
        """
        Ensure setup.py's _guard_py_ver aborts setup for an unsupported version
        """
        # NOTE: Adjust this when max_python_version in setup.py changes.
        unsupported_version = (3, 12, 0)
        unsupported_version_info = namedtuple(
            "version_info",
            (
                "major", "minor", "micro", "releaselevel",
                "serial", "n_fields", "n_sequence_fields", "n_unnamed_fields"
            )
        )(*unsupported_version, 'final', 0, 5, 5, 0)

        sys_version_info = sys.version_info

        # We run setup.py code! Since _guard_py_ver should fail, setup() should
        # never be invoked. But let's be extra sure it isn't and replace it.
        def failing_setup(*args, **kwargs):
            raise RuntimeError("This should not be reached!")

        distutils_core_setup = distutils.core.setup
        if setuptools:
            setuptools_setup = setuptools.setup

        spec = spec_from_file_location("__main__", str(setup_path))
        setup_module = module_from_spec(spec)
        try:
            sys.version_info = unsupported_version_info
            distutils.core.setup = failing_setup
            if setuptools:
                setuptools.setup = failing_setup

            msg = ("Cannot install on Python version {}; only versions "
                   ">=[0-9]+\\.[0-9]+,<[0-9]+\\.[0-9]+ are supported"
                   ).format(".".join(map(str, unsupported_version_info[:3])))
            with self.assertRaisesRegex(RuntimeError, msg):
                spec.loader.exec_module(setup_module)
        finally:
            # Restore anything we replaced.
            sys.version_info = sys_version_info
            distutils.core.setup = distutils_core_setup
            if setuptools:
                setuptools.setup = setuptools_setup


if __name__ == '__main__':
    unittest.main()
