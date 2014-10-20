from __future__ import print_function, absolute_import

import math
import unittest

from llvmlite.ir import Constant, FloatType, DoubleType
from . import TestCase


class TestValueRepr(TestCase):

    def test_double_repr(self):
        def check_repr(val, expected):
            c = Constant(DoubleType(), val)
            self.assertEqual(str(c), expected)
        check_repr(math.pi, "double 0x400921fb54442d18")
        check_repr(float('inf'), "double 0x7ff0000000000000")
        check_repr(float('-inf'), "double 0xfff0000000000000")

    def test_float_repr(self):
        def check_repr(val, expected):
            c = Constant(FloatType(), val)
            self.assertEqual(str(c), expected)
        check_repr(math.pi, "float 0x400921fb60000000")
        check_repr(float('inf'), "float 0x7ff0000000000000")
        check_repr(float('-inf'), "float 0xfff0000000000000")


if __name__ == "__main__":
    unittest.main()
