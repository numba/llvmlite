"""
Tests for legacy llvmpy-compatibility APIs.
"""

from __future__ import print_function, absolute_import

from . import TestCase


class TestMisc(TestCase):

    def test_imports(self):
        """
        Sanity-check llvmpy APIs import correctly.
        """
        from llvmlite.llvmpy.core import Constant, Type, Builder
        from llvmlite.llvmpy.passes import create_pass_manager_builder


if __name__ == '__main__':
    unittest.main()
