"""
IR Construction Tests
"""

from __future__ import print_function, absolute_import

import unittest
from . import TestCase
from llvmlite import ir
from llvmlite import binding as llvm
import re


class TestBase(TestCase):
    """Add a string matching test that ignores duplicated white space
    """

    def assertInText(self, pattern, text):
        """Replaces whitespace sequence in `pattern` with "\s+".
        """

        def escape(c):
            if not c.isalnum() and not c.isspace():
                return '\\' + c
            return c

        pattern = ''.join(map(escape, pattern))
        regex = re.sub(r'\s+', r'\s*', pattern)
        self.assertRegexpMatches(text, regex)

    def assert_valid_ir(self, mod):
        llvm.parse_assembly(str(mod))


class TestIR(TestBase):
    def module(self):
        return ir.Module()

    def test_metadata(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        pat = "!0 = metadata !{ i32 123 }"
        self.assertInText(pat, str(mod))
        self.assertInText(pat, str(md))
        self.assert_valid_ir(mod)

    def test_metadata_2(self):
        mod = self.module()
        mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        mod.add_metadata([ir.Constant(ir.IntType(32), 321)])
        pat1 = "!0 = metadata !{ i32 123 }"
        pat2 = "!1 = metadata !{ i32 321 }"
        self.assertInText(pat1, str(mod))
        self.assertInText(pat2, str(mod))

    def test_named_metadata(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        nmd = mod.add_named_metadata("foo")
        nmd.add(md)
        self.assertInText("!foo = !{ !0 }", str(mod))

    def test_named_metadata_2(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        nmd1 = mod.add_named_metadata("foo")
        nmd1.add(md)
        nmd2 = mod.add_named_metadata("bar")
        nmd2.add(md)
        nmd2.add(md)
        self.assertInText("!foo = !{ !0 }", str(mod))
        self.assertInText("!bar = !{ !0, !0 }", str(mod))

    def test_inline_assembly(self):
        mod = self.module()
        foo = ir.Function(mod, ir.FunctionType(ir.VoidType(), []), 'foo')
        builder = ir.IRBuilder(foo.append_basic_block(''))
        asmty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        asm = ir.InlineAsm(asmty, "mov $1, $2", "=r,r", side_effect=True)
        builder.call(asm, [ir.Constant(ir.IntType(32), 123)])
        builder.ret_void()
        pat = 'call i32 asm sideeffect "mov $1, $2", "=r,r" ( i32 123 )'
        self.assertInText(pat, str(mod))
        self.assert_valid_ir(mod)


if __name__ == '__main__':
    unittest.main()
