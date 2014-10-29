"""
IR Construction Tests
"""

from __future__ import print_function, absolute_import

import re
import textwrap
import unittest

from . import TestCase
from llvmlite import ir
from llvmlite import binding as llvm
from llvmlite import six

int32 = ir.IntType(32)


class TestBase(TestCase):
    """
    Utilities for IR tests.
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

    def module(self):
        return ir.Module()

    def function(self, module=None, name='my_func'):
        module = module or self.module()
        fnty = ir.FunctionType(int32, (int32, int32))
        return ir.Function(self.module(), fnty, name)

    def block(self, func=None, name=''):
        func = func or self.function()
        return ir.Block(func, name)

    def descr(self, thing):
        sio = six.StringIO()
        thing.descr(sio)
        return sio.getvalue()


class TestIR(TestBase):

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


class TestBlock(TestBase):

    def test_attributes(self):
        func = self.function()
        block = ir.Block(parent=func, name='start')
        self.assertIs(block.parent, func)
        self.assertFalse(block.is_terminated)

    def test_descr(self):
        block = self.block(name='my_block')
        self.assertEqual(self.descr(block), "my_block:\n")
        block.instructions.extend(['a', 'b'])
        self.assertEqual(self.descr(block), "my_block:\n  a\n  b\n")


class TestBuilder(TestBase):

    def check_block(self, block, asm):
        asm = textwrap.dedent(asm)
        # Normalize indent
        asm = asm.replace("\n    ", "\n  ")
        self.assertEqual(self.descr(block), asm)

    def test_attributes(self):
        block = self.block(name='start')
        builder = ir.IRBuilder(block)
        self.assertIs(builder.function, block.parent)

    def test_simple(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.add(a, b, 'res')
        self.check_block(block, """\
            my_block:
                %"res" = add i32 %".1", %".2"
            """)

    def test_binops(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.add(a, b, 'c')
        builder.fadd(a, b, 'd')
        builder.sub(a, b, 'e')
        builder.fsub(a, b, 'f')
        builder.mul(a, b, 'g')
        builder.fmul(a, b, 'h')
        builder.udiv(a, b, 'i')
        builder.sdiv(a, b, 'j')
        builder.fdiv(a, b, 'k')
        builder.urem(a, b, 'l')
        builder.srem(a, b, 'm')
        builder.frem(a, b, 'n')
        builder.or_(a, b, 'o')
        builder.and_(a, b, 'p')
        builder.xor(a, b, 'q')
        builder.shl(a, b, 'r')
        builder.ashr(a, b, 's')
        builder.lshr(a, b, 't')
        self.check_block(block, """\
            my_block:
                %"c" = add i32 %".1", %".2"
                %"d" = fadd i32 %".1", %".2"
                %"e" = sub i32 %".1", %".2"
                %"f" = fsub i32 %".1", %".2"
                %"g" = mul i32 %".1", %".2"
                %"h" = fmul i32 %".1", %".2"
                %"i" = udiv i32 %".1", %".2"
                %"j" = sdiv i32 %".1", %".2"
                %"k" = fdiv i32 %".1", %".2"
                %"l" = urem i32 %".1", %".2"
                %"m" = srem i32 %".1", %".2"
                %"n" = frem i32 %".1", %".2"
                %"o" = or i32 %".1", %".2"
                %"p" = and i32 %".1", %".2"
                %"q" = xor i32 %".1", %".2"
                %"r" = shl i32 %".1", %".2"
                %"s" = ashr i32 %".1", %".2"
                %"t" = lshr i32 %".1", %".2"
            """)


if __name__ == '__main__':
    unittest.main()
