"""
IR Construction Tests
"""

from __future__ import print_function, absolute_import

import copy
import itertools
import re
import textwrap
import unittest

from . import TestCase
from llvmlite import ir
from llvmlite import binding as llvm
from llvmlite import six


int1 = ir.IntType(1)
int8 = ir.IntType(8)
int32 = ir.IntType(32)
int64 = ir.IntType(64)
flt = ir.FloatType()
dbl = ir.DoubleType()


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
        fnty = ir.FunctionType(int32, (int32, int32, dbl, ir.PointerType(int32)))
        return ir.Function(self.module(), fnty, name)

    def block(self, func=None, name=''):
        func = func or self.function()
        return func.append_basic_block(name)

    def descr(self, thing):
        sio = six.StringIO()
        thing.descr(sio)
        return sio.getvalue()

    def check_descr(self, descr, expected):
        expected = textwrap.dedent(expected)
        # Normalize indent
        expected = expected.replace("\n    ", "\n  ")
        self.assertEqual(descr, expected)

    def check_block(self, block, asm):
        self.check_descr(self.descr(block), asm)


class TestFunction(TestBase):

    proto = """i32 @"my_func"(i32 %".1", i32 %".2", double %".3", i32* %".4")"""

    def test_declare(self):
        # A simple declaration
        func = self.function()
        asm = self.descr(func).strip()
        self.assertEqual(asm.strip(), "declare %s" % self.proto)

    def test_declare_attributes(self):
        # Now with function attributes
        func = self.function()
        func.attributes.add("optsize")
        func.attributes.add("alwaysinline")
        func.attributes.alignstack = 16
        asm = self.descr(func).strip()
        self.assertEqual(asm,
            "declare %s alwaysinline optsize alignstack(16)" % self.proto)

    def test_define(self):
        # A simple definition
        func = self.function()
        func.attributes.add("alwaysinline")
        block = func.append_basic_block('my_block')
        builder = ir.IRBuilder(block)
        builder.ret_void()
        asm = self.descr(func)
        self.check_descr(asm, """\
            define {proto} alwaysinline
            {{
            my_block:
                ret void
            }}
            """.format(proto=self.proto))


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

    def test_replace(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        c = builder.add(a, b, 'c')
        d = builder.sub(a, b, 'd')
        builder.mul(d, b, 'e')
        f = ir.Instruction(block, a.type, 'sdiv', (c, b), 'f')
        block.replace(d, f)
        self.check_block(block, """\
            my_block:
                %"c" = add i32 %".1", %".2"
                %"f" = sdiv i32 %"c", %".2"
                %"e" = mul i32 %"f", %".2"
            """)


class TestBuilder(TestBase):
    """
    Test IR generation through the builder class.
    """

    def test_attributes(self):
        block = self.block(name='start')
        builder = ir.IRBuilder(block)
        self.assertIs(builder.function, block.parent)

    def test_constant(self):
        """
        Test the IRBuilder.constant() method.
        """
        block = self.block(name='start')
        builder = ir.IRBuilder(block)
        c = builder.constant(int32, 5)
        self.assertIsInstance(c, ir.Constant)
        self.assertIs(c.type, int32)
        self.assertEqual(c.constant, 5)

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
        self.assertFalse(block.is_terminated)
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

    def test_unary_ops(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.neg(a, 'c')
        builder.not_(b, 'd')
        self.assertFalse(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"c" = sub i32 0, %".1"
                %"d" = xor i32 %".2", -1
            """)

    def test_integer_comparisons(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.icmp_unsigned('==', a, b, 'c')
        builder.icmp_unsigned('!=', a, b, 'd')
        builder.icmp_unsigned('<', a, b, 'e')
        builder.icmp_unsigned('<=', a, b, 'f')
        builder.icmp_unsigned('>', a, b, 'g')
        builder.icmp_unsigned('>=', a, b, 'h')
        builder.icmp_signed('==', a, b, 'i')
        builder.icmp_signed('!=', a, b, 'j')
        builder.icmp_signed('<', a, b, 'k')
        builder.icmp_signed('<=', a, b, 'l')
        builder.icmp_signed('>', a, b, 'm')
        builder.icmp_signed('>=', a, b, 'n')
        with self.assertRaises(ValueError):
            builder.icmp_signed('uno', a, b, 'zz')
        with self.assertRaises(ValueError):
            builder.icmp_signed('foo', a, b, 'zz')
        self.assertFalse(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"c" = icmp eq i32 %".1", %".2"
                %"d" = icmp ne i32 %".1", %".2"
                %"e" = icmp ult i32 %".1", %".2"
                %"f" = icmp ule i32 %".1", %".2"
                %"g" = icmp ugt i32 %".1", %".2"
                %"h" = icmp uge i32 %".1", %".2"
                %"i" = icmp eq i32 %".1", %".2"
                %"j" = icmp ne i32 %".1", %".2"
                %"k" = icmp slt i32 %".1", %".2"
                %"l" = icmp sle i32 %".1", %".2"
                %"m" = icmp sgt i32 %".1", %".2"
                %"n" = icmp sge i32 %".1", %".2"
            """)

    def test_float_comparisons(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.fcmp_ordered('==', a, b, 'c')
        builder.fcmp_ordered('!=', a, b, 'd')
        builder.fcmp_ordered('<', a, b, 'e')
        builder.fcmp_ordered('<=', a, b, 'f')
        builder.fcmp_ordered('>', a, b, 'g')
        builder.fcmp_ordered('>=', a, b, 'h')
        builder.fcmp_unordered('==', a, b, 'i')
        builder.fcmp_unordered('!=', a, b, 'j')
        builder.fcmp_unordered('<', a, b, 'k')
        builder.fcmp_unordered('<=', a, b, 'l')
        builder.fcmp_unordered('>', a, b, 'm')
        builder.fcmp_unordered('>=', a, b, 'n')
        # fcmp_ordered and fcmp_unordered are the same for these cases
        builder.fcmp_ordered('ord', a, b, 'u')
        builder.fcmp_ordered('uno', a, b, 'v')
        builder.fcmp_unordered('ord', a, b, 'w')
        builder.fcmp_unordered('uno', a, b, 'x')
        self.assertFalse(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"c" = fcmp oeq i32 %".1", %".2"
                %"d" = fcmp one i32 %".1", %".2"
                %"e" = fcmp olt i32 %".1", %".2"
                %"f" = fcmp ole i32 %".1", %".2"
                %"g" = fcmp ogt i32 %".1", %".2"
                %"h" = fcmp oge i32 %".1", %".2"
                %"i" = fcmp ueq i32 %".1", %".2"
                %"j" = fcmp une i32 %".1", %".2"
                %"k" = fcmp ult i32 %".1", %".2"
                %"l" = fcmp ule i32 %".1", %".2"
                %"m" = fcmp ugt i32 %".1", %".2"
                %"n" = fcmp uge i32 %".1", %".2"
                %"u" = fcmp ord i32 %".1", %".2"
                %"v" = fcmp uno i32 %".1", %".2"
                %"w" = fcmp ord i32 %".1", %".2"
                %"x" = fcmp uno i32 %".1", %".2"
            """)

    def test_misc_ops(self):
        block = self.block(name='my_block')
        t = ir.Constant(int1, True)
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.select(t, a, b, 'c')
        self.assertFalse(block.is_terminated)
        builder.unreachable()
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"c" = select i1 true, i32 %".1", i32 %".2"
                unreachable
            """)

    def test_phi(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        bb2 = builder.function.append_basic_block('b2')
        bb3 = builder.function.append_basic_block('b3')
        phi = builder.phi(int32, 'my_phi')
        phi.add_incoming(a, bb2)
        phi.add_incoming(b, bb3)
        self.assertFalse(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"my_phi" = phi i32 [%".1", %"b2"], [%".2", %"b3"]
            """)

    def test_mem_ops(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        c = builder.alloca(int32, name='c')
        d = builder.alloca(int32, size=42, name='d')
        e = builder.alloca(int32, size=a, name='e')
        self.assertEqual(e.type, ir.PointerType(int32))
        f = builder.store(b, c)
        self.assertEqual(f.type, ir.VoidType())
        g = builder.load(c, 'g')
        self.assertEqual(g.type, int32)
        with self.assertRaises(TypeError):
            builder.store(b, a)
        with self.assertRaises(TypeError):
            builder.load(b)
        self.check_block(block, """\
            my_block:
                %"c" = alloca i32
                %"d" = alloca i32, i32 42
                %"e" = alloca i32, i32 %".1"
                store i32 %".2", i32* %"c"
                %"g" = load i32* %"c"
            """)

    def test_gep(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        c = builder.alloca(ir.PointerType(int32), name='c')
        d = builder.gep(c, [ir.Constant(int32, 5), a], name='d')
        self.assertEqual(d.type, ir.PointerType(int32))
        self.check_block(block, """\
            my_block:
                %"c" = alloca i32*
                %"d" = getelementptr i32** %"c", i32 5, i32 %".1"
            """)
        # XXX test with more complex types

    def test_extract_insert_value(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        tp_inner = ir.LiteralStructType([int32, int1])
        tp_outer = ir.LiteralStructType([int8, tp_inner])
        c_inner = ir.Constant(tp_inner, (ir.Constant(int32, 4),
                                         ir.Constant(int1, True)))
        # Flat structure
        c = builder.extract_value(c_inner, 0, name='c')
        d = builder.insert_value(c_inner, a, 0, name='d')
        e = builder.insert_value(d, ir.Constant(int1, False), 1, name='e')
        self.assertEqual(d.type, tp_inner)
        self.assertEqual(e.type, tp_inner)
        # Nested structure
        p_outer = builder.alloca(tp_outer, name='ptr')
        j = builder.load(p_outer, name='j')
        k = builder.extract_value(j, 0, name='k')
        l = builder.extract_value(j, 1, name='l')
        m = builder.extract_value(j, (1, 0), name='m')
        n = builder.extract_value(j, (1, 1), name='n')
        o = builder.insert_value(j, l, 1, name='o')
        p = builder.insert_value(j, a, (1, 0), name='p')
        self.assertEqual(k.type, int8)
        self.assertEqual(l.type, tp_inner)
        self.assertEqual(m.type, int32)
        self.assertEqual(n.type, int1)
        self.assertEqual(o.type, tp_outer)
        self.assertEqual(p.type, tp_outer)

        with self.assertRaises(TypeError):
            # Not an aggregate
            builder.extract_value(p_outer, 0)
        with self.assertRaises(TypeError):
            # Indexing too deep
            builder.extract_value(c_inner, (0, 0))
        with self.assertRaises(TypeError):
            # Index out of structure bounds
            builder.extract_value(c_inner, 5)
        with self.assertRaises(TypeError):
            # Not an aggregate
            builder.insert_value(a, b, 0)
        with self.assertRaises(TypeError):
            # Replacement value has the wrong type
            builder.insert_value(c_inner, a, 1)

        self.check_block(block, """\
            my_block:
                %"c" = extractvalue {i32, i1} {i32 4, i1 true}, 0
                %"d" = insertvalue {i32, i1} {i32 4, i1 true}, i32 %".1", 0
                %"e" = insertvalue {i32, i1} %"d", i1 false, 1
                %"ptr" = alloca {i8, {i32, i1}}
                %"j" = load {i8, {i32, i1}}* %"ptr"
                %"k" = extractvalue {i8, {i32, i1}} %"j", 0
                %"l" = extractvalue {i8, {i32, i1}} %"j", 1
                %"m" = extractvalue {i8, {i32, i1}} %"j", 1, 0
                %"n" = extractvalue {i8, {i32, i1}} %"j", 1, 1
                %"o" = insertvalue {i8, {i32, i1}} %"j", {i32, i1} %"l", 1
                %"p" = insertvalue {i8, {i32, i1}} %"j", i32 %".1", 1, 0
            """)

    def test_cast_ops(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b, fa, ptr = builder.function.args[:4]
        c = builder.trunc(a, int8, name='c')
        d = builder.zext(c, int32, name='d')
        e = builder.sext(c, int32, name='e')
        fb = builder.fptrunc(fa, flt, 'fb')
        fc = builder.fpext(fb, dbl, 'fc')
        g = builder.fptoui(fa, int32, 'g')
        h = builder.fptosi(fa, int8, 'h')
        fd = builder.uitofp(g, flt, 'fd')
        fe = builder.sitofp(h, dbl, 'fe')
        i = builder.ptrtoint(ptr, int32, 'i')
        j = builder.inttoptr(i, ir.PointerType(int8), 'j')
        k = builder.bitcast(a, flt, "k")
        self.assertFalse(block.is_terminated)
        self.check_block(block, """\
            my_block:
                %"c" = trunc i32 %".1" to i8
                %"d" = zext i8 %"c" to i32
                %"e" = sext i8 %"c" to i32
                %"fb" = fptrunc double %".3" to float
                %"fc" = fpext float %"fb" to double
                %"g" = fptoui double %".3" to i32
                %"h" = fptosi double %".3" to i8
                %"fd" = uitofp i32 %"g" to float
                %"fe" = sitofp i8 %"h" to double
                %"i" = ptrtoint i32* %".4" to i32
                %"j" = inttoptr i32 %"i" to i8*
                %"k" = bitcast i32 %".1" to float
            """)

    def test_atomicrmw(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        c = builder.alloca(int32, name='c')
        d = builder.atomic_rmw('add', c, a, 'monotonic', 'd')
        self.assertEqual(d.type, int32)
        self.check_block(block, """\
            my_block:
                %"c" = alloca i32
                %"d" = atomicrmw add i32* %"c", i32 %".1" monotonic
            """)

    def test_branch(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        bb_target = builder.function.append_basic_block(name='target')
        builder.branch(bb_target)
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                br label %"target"
            """)

    def test_cbranch(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        bb_true = builder.function.append_basic_block(name='b_true')
        bb_false = builder.function.append_basic_block(name='b_false')
        builder.cbranch(ir.Constant(int1, False), bb_true, bb_false)
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                br i1 false, label %"b_true", label %"b_false"
            """)

    def test_returns(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        builder.ret_void()
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                ret void
            """)
        block = self.block(name='other_block')
        builder = ir.IRBuilder(block)
        builder.ret(ir.Constant(int32, 5))
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            other_block:
                ret i32 5
            """)

    def test_switch(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        bb_onzero = builder.function.append_basic_block(name='onzero')
        bb_onone = builder.function.append_basic_block(name='onone')
        bb_ontwo = builder.function.append_basic_block(name='ontwo')
        bb_else = builder.function.append_basic_block(name='otherwise')
        sw = builder.switch(a, bb_else)
        sw.add_case(ir.Constant(int32, 0), bb_onzero)
        sw.add_case(ir.Constant(int32, 1), bb_onone)
        sw.add_case(ir.Constant(int32, 2), bb_ontwo)
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                switch i32 %".1", label %"otherwise" [i32 0, label %"onzero" i32 1, label %"onone" i32 2, label %"ontwo"]
            """)

    def test_call(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        tp_f = ir.FunctionType(flt, (int32, int32))
        tp_g = ir.FunctionType(dbl, (int32,), var_arg=True)
        f = ir.Function(builder.function.module, tp_f, 'f')
        g = ir.Function(builder.function.module, tp_g, 'g')
        builder.call(f, (a, b), 'res_f')
        builder.call(g, (b, a), 'res_g')
        builder.call(f, (a, b), 'res_f_fast', cconv='fastcc')
        self.check_block(block, """\
            my_block:
                %"res_f" = call float (i32, i32)* @"f"(i32 %".1", i32 %".2")
                %"res_g" = call double (i32, ...)* @"g"(i32 %".2", i32 %".1")
                %"res_f_fast" = call fastcc float (i32, i32)* @"f"(i32 %".1", i32 %".2")
            """)

    def test_positioning(self):
        """
        Test IRBuilder.position_{before,after,at_start,at_end}.
        """
        func = self.function()
        builder = ir.IRBuilder()
        z = ir.Constant(int32, 0)
        bb_one = func.append_basic_block(name='one')
        bb_two = func.append_basic_block(name='two')
        bb_three = func.append_basic_block(name='three')
        # .at_start(empty block)
        builder.position_at_start(bb_one)
        a = builder.add(z, z, 'a')
        # .at_end(empty block)
        builder.position_at_end(bb_two)
        m = builder.add(z, z, 'm')
        n = builder.add(z, z, 'n')
        # .at_start(block)
        builder.position_at_start(bb_two)
        o = builder.add(z, z, 'o')
        p = builder.add(z, z, 'p')
        # .at_end(block)
        builder.position_at_end(bb_one)
        b = builder.add(z, z, 'b')
        # .after(instr)
        builder.position_after(o)
        q = builder.add(z, z, 'q')
        # .before(instr)
        builder.position_before(b)
        c = builder.add(z, z, 'c')
        self.check_block(bb_one, """\
            one:
                %"a" = add i32 0, 0
                %"c" = add i32 0, 0
                %"b" = add i32 0, 0
            """)
        self.check_block(bb_two, """\
            two:
                %"o" = add i32 0, 0
                %"q" = add i32 0, 0
                %"p" = add i32 0, 0
                %"m" = add i32 0, 0
                %"n" = add i32 0, 0
            """)
        self.check_block(bb_three, """\
            three:
            """)


class TestTypes(TestBase):

    def test_comparisons(self):
        # A bunch of mutually unequal types
        types = [
            ir.LabelType(), ir.VoidType(),
            ir.FunctionType(int1, (int8, int8)), ir.FunctionType(int1, (int8,)),
            ir.FunctionType(int1, (int8,), var_arg=True),
            ir.FunctionType(int8, (int8,)),
            int1, int8, int32, flt, dbl,
            ir.ArrayType(flt, 5), ir.ArrayType(dbl, 5), ir.ArrayType(dbl, 4),
            ir.LiteralStructType((int1, int8)), ir.LiteralStructType((int8, int1)),
            ]
        types.extend([ir.PointerType(tp) for tp in types
                      if not isinstance(tp, ir.VoidType)])
        for a, b in itertools.product(types, types):
            if a is not b:
                self.assertFalse(a == b, (a, b))
                self.assertTrue(a != b, (a, b))
        # We assume copy.copy() works fine here...
        for tp in types:
            other = copy.copy(tp)
            self.assertIsNot(other, tp)
            if isinstance(tp, ir.LabelType):
                self.assertFalse(tp == other, (tp, other))
                self.assertTrue(tp != other, (tp, other))
            else:
                self.assertTrue(tp == other, (tp, other))
                self.assertFalse(tp != other, (tp, other))

    def test_str(self):
        """
        Test the string representation of types.
        """
        self.assertEqual(str(int1), 'i1')
        self.assertEqual(str(ir.IntType(29)), 'i29')
        self.assertEqual(str(flt), 'float')
        self.assertEqual(str(dbl), 'double')
        self.assertEqual(str(ir.VoidType()), 'void')
        self.assertEqual(str(ir.FunctionType(int1, ())), 'i1 ()')
        self.assertEqual(str(ir.FunctionType(int1, (flt,))), 'i1 (float)')
        self.assertEqual(str(ir.FunctionType(int1, (flt, dbl))),
                         'i1 (float, double)')
        self.assertEqual(str(ir.FunctionType(int1, (), var_arg=True)),
                         'i1 (...)')
        self.assertEqual(str(ir.FunctionType(int1, (flt,), var_arg=True)),
                         'i1 (float, ...)')
        self.assertEqual(str(ir.FunctionType(int1, (flt, dbl), var_arg=True)),
                         'i1 (float, double, ...)')
        self.assertEqual(str(ir.PointerType(int32)), 'i32*')
        self.assertEqual(str(ir.PointerType(ir.PointerType(int32))), 'i32**')
        self.assertEqual(str(ir.ArrayType(int1, 5)), '[5 x i1]')
        self.assertEqual(str(ir.ArrayType(ir.PointerType(int1), 5)), '[5 x i1*]')
        self.assertEqual(str(ir.PointerType(ir.ArrayType(int1, 5))), '[5 x i1]*')
        self.assertEqual(str(ir.LiteralStructType((int1,))), '{i1}')
        self.assertEqual(str(ir.LiteralStructType((int1, flt))), '{i1, float}')
        self.assertEqual(str(ir.LiteralStructType((
            ir.PointerType(int1), ir.LiteralStructType((int32, int8))))),
            '{i1*, {i32, i8}}')

        # Avoid polluting the namespace
        context = ir.Context()
        mytype = context.get_identified_type("MyType")
        self.assertEqual(str(mytype), "%MyType")

    def test_gep(self):
        def check_constant(tp, i, expected):
            actual = tp.gep(ir.Constant(int32, i))
            self.assertEqual(actual, expected)
        def check_index_type(tp):
            index = ir.Constant(dbl, 1.0)
            with self.assertRaises(TypeError):
                tp.gep(index)

        tp = ir.PointerType(dbl)
        for i in range(5):
            check_constant(tp, i, dbl)
        check_index_type(tp)

        tp = ir.ArrayType(int1, 3)
        for i in range(3):
            check_constant(tp, i, int1)
        check_index_type(tp)

        tp = ir.LiteralStructType((dbl, ir.LiteralStructType((int1, int8))))
        check_constant(tp, 0, dbl)
        check_constant(tp, 1, ir.LiteralStructType((int1, int8)))
        with self.assertRaises(IndexError):
            tp.gep(ir.Constant(int32, 2))
        check_index_type(tp)

    def test_abi_size(self):
        td = llvm.create_target_data("e-m:e-i64:64-f80:128-n8:16:32:64-S128")
        def check(tp, expected):
            self.assertEqual(tp.get_abi_size(td), expected)
        check(int8, 1)
        check(int32, 4)
        check(int64, 8)
        check(ir.ArrayType(int8, 5), 5)
        check(ir.ArrayType(int32, 5), 20)
        check(ir.LiteralStructType((dbl, flt, flt)), 16)

    def test_identified_struct(self):
        context = ir.Context()
        mytype = context.get_identified_type("MyType")
        module = ir.Module(context=context)
        self.assertTrue(mytype.is_opaque)
        self.assert_valid_ir(module)
        oldstr = str(module)
        mytype.set_body(ir.IntType(32), ir.IntType(64), ir.FloatType())
        self.assertFalse(mytype.is_opaque)
        self.assert_valid_ir(module)
        self.assertNotEqual(oldstr, str(module))


c32 = lambda i: ir.Constant(int32, i)


class TestConstant(TestBase):

    def test_integers(self):
        c = ir.Constant(int32, 42)
        self.assertEqual(str(c), 'i32 42')
        c = ir.Constant(int1, 1)
        self.assertEqual(str(c), 'i1 1')
        c = ir.Constant(int1, 0)
        self.assertEqual(str(c), 'i1 0')
        c = ir.Constant(int1, True)
        self.assertEqual(str(c), 'i1 true')
        c = ir.Constant(int1, False)
        self.assertEqual(str(c), 'i1 false')
        c = ir.Constant(int1, ir.Undefined)
        self.assertEqual(str(c), 'i1 undef')

    def test_reals(self):
        # XXX Test NaNs and infs
        c = ir.Constant(flt, 1.5)
        self.assertEqual(str(c), 'float 0x3ff8000000000000')
        c = ir.Constant(flt, -1.5)
        self.assertEqual(str(c), 'float 0xbff8000000000000')
        c = ir.Constant(dbl, 1.5)
        self.assertEqual(str(c), 'double 0x3ff8000000000000')
        c = ir.Constant(dbl, -1.5)
        self.assertEqual(str(c), 'double 0xbff8000000000000')
        c = ir.Constant(dbl, ir.Undefined)
        self.assertEqual(str(c), 'double undef')

    def test_arrays(self):
        # XXX Test byte array special case
        c = ir.Constant(ir.ArrayType(int32, 3), (c32(5), c32(6), c32(4)))
        self.assertEqual(str(c), '[3 x i32] [i32 5, i32 6, i32 4]')
        c = ir.Constant(ir.ArrayType(int32, 2), (c32(5), c32(ir.Undefined)))
        self.assertEqual(str(c), '[2 x i32] [i32 5, i32 undef]')
        c = ir.Constant(ir.ArrayType(int32, 2), ir.Undefined)
        self.assertEqual(str(c), '[2 x i32] undef')

    def test_structs(self):
        c = ir.Constant(ir.LiteralStructType((flt, int1)),
                        (ir.Constant(ir.FloatType(), 1.5),
                         ir.Constant(int1, True)))
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c = ir.Constant.literal_struct((ir.Constant(ir.FloatType(), 1.5),
                                        ir.Constant(int1, True)))
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c = ir.Constant.literal_struct((ir.Constant(ir.FloatType(), 1.5),
                                        ir.Constant(int1, ir.Undefined)))
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 undef}')
        c = ir.Constant(ir.LiteralStructType((flt, int1)), ir.Undefined)
        self.assertEqual(str(c), '{float, i1} undef')


class TestTransforms(TestBase):
    def test_call_transform(self):
        mod = ir.Module()
        foo = ir.Function(mod, ir.FunctionType(ir.VoidType(), ()), "foo")
        bar = ir.Function(mod, ir.FunctionType(ir.VoidType(), ()), "bar")
        builder = ir.IRBuilder()
        builder.position_at_end(foo.append_basic_block())
        call = builder.call(foo, ())
        self.assertEqual(call.callee, foo)
        modified = ir.replace_all_calls(mod, foo, bar)
        self.assertIn(call, modified)
        self.assertNotEqual(call.callee, foo)
        self.assertEqual(call.callee, bar)


if __name__ == '__main__':
    unittest.main()
