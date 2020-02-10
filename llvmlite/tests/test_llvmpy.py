"""
Tests for legacy llvmpy-compatibility APIs.
"""

from llvmlite.tests import TestCase


class TestMisc(TestCase):

    def test_imports(self):
        """
        Sanity-check llvmpy APIs import correctly.
        """
        from llvmlite.llvmpy.core import Constant, Type, Builder
        from llvmlite.llvmpy.passes import create_pass_manager_builder


if __name__ == '__main__':
    unittest.main()
