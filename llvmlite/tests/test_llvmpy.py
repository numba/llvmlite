"""
Tests for legacy llvmpy-compatibility APIs.
"""

import unittest
from llvmlite.tests import TestCase


class TestMisc(TestCase):

    def test_imports(self):
        """
        Sanity-check llvmpy APIs import correctly.
        """
        from llvmlite.llvmpy.core import Constant, Type, Builder  # noqa F401
        from llvmlite.llvmpy.passes import create_pass_manager_builder  # noqa F401 E501


if __name__ == '__main__':
    unittest.main()
