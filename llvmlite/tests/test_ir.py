"""
IR Construction Tests
"""

from __future__ import print_function, absolute_import

import copy
import itertools
import pickle
import re
import textwrap
import unittest
from array import array

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
        buf = []
        thing.descr(buf)
        return "".join(buf)

    def _normalize_asm(self, asm):
        asm = textwrap.dedent(asm)
        # Normalize indent
        asm = asm.replace("\n    ", "\n  ")
        return asm

    def check_descr(self, descr, asm):
        expected = self._normalize_asm(asm)
        self.assertEqual(descr, expected)

    def check_block(self, block, asm):
        self.check_descr(self.descr(block), asm)

    def check_metadata(self, module, asm):
        """
        Check module metadata against *asm*.
        """
        expected = self._normalize_asm(asm)
        actual = module._stringify_metadata()
        self.assertEqual(actual.strip(), expected.strip())

    def check_func_body(self, func, asm):
        expected = self._normalize_asm(asm)
        actual = self.descr(func)
        actual = actual.partition('{')[2].rpartition('}')[0]
        self.assertEqual(actual.strip(), expected.strip())


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
        tp_pers = ir.FunctionType(int8, (), var_arg=True)
        pers = ir.Function(self.module(), tp_pers, '__gxx_personality_v0')
        func.attributes.personality = pers
        asm = self.descr(func).strip()
        self.assertEqual(asm,
            ("declare %s alwaysinline optsize alignstack(16) "
             "personality i8 (...)* @\"__gxx_personality_v0\"") % self.proto)

    def test_function_attributes(self):
        # Now with parameter attributes
        func = self.function()
        func.args[0].add_attribute("zeroext")
        func.args[3].add_attribute("nonnull")
        func.return_value.add_attribute("noalias")
        asm = self.descr(func).strip()
        self.assertEqual(asm,
            """declare noalias i32 @"my_func"(i32 zeroext %".1", i32 %".2", double %".3", i32* nonnull %".4")"""
            )

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

    def test_declare_intrinsics(self):
        module = self.module()
        pint8 = int8.as_pointer()

        powi = module.declare_intrinsic('llvm.powi', [dbl])
        memset = module.declare_intrinsic('llvm.memset', [pint8, int32])
        memcpy = module.declare_intrinsic('llvm.memcpy', [pint8, pint8, int32])
        assume = module.declare_intrinsic('llvm.assume')
        self.check_descr(self.descr(powi).strip(), """\
            declare double @"llvm.powi.f64"(double %".1", i32 %".2")""")
        self.check_descr(self.descr(memset).strip(), """\
            declare void @"llvm.memset.p0i8.i32"(i8* %".1", i8 %".2", i32 %".3", i32 %".4", i1 %".5")""")
        self.check_descr(self.descr(memcpy).strip(), """\
            declare void @"llvm.memcpy.p0i8.p0i8.i32"(i8* %".1", i8* %".2", i32 %".3", i32 %".4", i1 %".5")""")
        self.check_descr(self.descr(assume).strip(), """\
            declare void @"llvm.assume"(i1 %".1")""")

    def test_redeclare_intrinsic(self):
        module = self.module()
        powi = module.declare_intrinsic('llvm.powi', [dbl])
        powi2 = module.declare_intrinsic('llvm.powi', [dbl])
        self.assertIs(powi, powi2)


class TestIR(TestBase):

    def test_globals_access(self):
        mod = self.module()
        foo = ir.Function(mod, ir.FunctionType(ir.VoidType(), []), 'foo')
        ir.Function(mod, ir.FunctionType(ir.VoidType(), []), 'bar')
        globdouble = ir.GlobalVariable(mod, ir.DoubleType(), 'globdouble')
        self.assertEqual(mod.get_global('foo'), foo)
        self.assertEqual(mod.get_global('globdouble'), globdouble)
        self.assertIsNone(mod.get_global('kkk'))
        # Globals should have a useful repr()
        self.assertEqual(repr(globdouble),
                         "<ir.GlobalVariable 'globdouble' of type 'double*'>")

    def test_functions_global_values_access(self):
        mod = self.module()
        fty = ir.FunctionType(ir.VoidType(), [])
        foo = ir.Function(mod, fty, 'foo')
        bar = ir.Function(mod, fty, 'bar')
        globdouble = ir.GlobalVariable(mod, ir.DoubleType(), 'globdouble')
        self.assertEqual(set(mod.functions), set((foo, bar)))
        self.assertEqual(set(mod.global_values), set((foo, bar, globdouble)))

    def test_metadata(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        pat = "!0 = !{ i32 123 }"
        self.assertInText(pat, str(mod))
        self.assertInText(pat, str(md))
        self.assert_valid_ir(mod)

    def test_metadata_2(self):
        mod = self.module()
        mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        mod.add_metadata([ir.Constant(ir.IntType(32), 321),
                          ir.MetaDataString(mod, "kernel")])
        pat1 = "!0 = !{ i32 123 }"
        pat2 = '!1 = !{ i32 321, !"kernel" }'
        self.assertInText(pat1, str(mod))
        self.assertInText(pat2, str(mod))

    def test_named_metadata(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.IntType(32), 123)])
        nmd = mod.add_named_metadata("foo")
        nmd.add(md)
        self.assertInText("!foo = !{ !0 }", str(mod))
        self.assert_valid_ir(mod)

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
        self.assert_valid_ir(mod)

    def test_metadata_null(self):
        mod = self.module()
        md = mod.add_metadata([ir.Constant(ir.PointerType(ir.IntType(32)), None)])
        self.assertInText("!{ i32* null }", str(mod))
        self.assert_valid_ir(mod)

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

    def test_repr(self):
        """
        Blocks should have a useful repr()
        """
        func = self.function()
        block = ir.Block(parent=func, name='start')
        self.assertEqual(repr(block), "<ir.Block 'start' of type 'label'>")


class TestBuildInstructions(TestBase):
    """
    Test IR generation of LLVM instructions through the IRBuilder class.
    """

    maxDiff = 4000

    def test_simple(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        inst = builder.add(a, b, 'res')
        self.check_block(block, """\
            my_block:
                %"res" = add i32 %".1", %".2"
            """)
        # Instructions should have a useful repr()
        self.assertEqual(repr(inst),
                         "<ir.Instruction 'res' of type 'i32', opname 'add', "
                         "operands (<ir.Argument '.1' of type i32>, <ir.Argument '.2' of type i32>)>")

    def test_binops(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b, ff = builder.function.args[:3]
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
        with self.assertRaises(ValueError) as cm:
            builder.add(a, ff)
        self.assertEqual(str(cm.exception),
                         "Operands must be the same type, got (i32, double)")
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

    def test_binop_flags(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        # As tuple
        builder.add(a, b, 'c', flags=('nuw',))
        # and as list
        builder.sub(a, b, 'd', flags=['nuw', 'nsw'])
        self.check_block(block, """\
            my_block:
                %"c" = add nuw i32 %".1", %".2"
                %"d" = sub nuw nsw i32 %".1", %".2"
            """)

    def test_binops_with_overflow(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.sadd_with_overflow(a, b, 'c')
        builder.smul_with_overflow(a, b, 'd')
        builder.ssub_with_overflow(a, b, 'e')
        builder.uadd_with_overflow(a, b, 'f')
        builder.umul_with_overflow(a, b, 'g')
        builder.usub_with_overflow(a, b, 'h')
        self.check_block(block, """\
            my_block:
                %"c" = call {i32, i1} (i32, i32) @"llvm.sadd.with.overflow.i32"(i32 %".1", i32 %".2")
                %"d" = call {i32, i1} (i32, i32) @"llvm.smul.with.overflow.i32"(i32 %".1", i32 %".2")
                %"e" = call {i32, i1} (i32, i32) @"llvm.ssub.with.overflow.i32"(i32 %".1", i32 %".2")
                %"f" = call {i32, i1} (i32, i32) @"llvm.uadd.with.overflow.i32"(i32 %".1", i32 %".2")
                %"g" = call {i32, i1} (i32, i32) @"llvm.umul.with.overflow.i32"(i32 %".1", i32 %".2")
                %"h" = call {i32, i1} (i32, i32) @"llvm.usub.with.overflow.i32"(i32 %".1", i32 %".2")
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
        a, b, z = builder.function.args[:3]
        c = builder.alloca(int32, name='c')
        d = builder.alloca(int32, size=42, name='d')
        e = builder.alloca(dbl, size=a, name='e')
        self.assertEqual(e.type, ir.PointerType(dbl))
        ee = builder.store(z, e)
        self.assertEqual(ee.type, ir.VoidType())
        f = builder.store(b, c)
        self.assertEqual(f.type, ir.VoidType())
        g = builder.load(c, 'g')
        self.assertEqual(g.type, int32)
        # With alignment
        h = builder.store(b, c, align=1)
        self.assertEqual(h.type, ir.VoidType())
        i = builder.load(c, 'i', align=1)
        self.assertEqual(i.type, int32)
        # Not pointer types
        with self.assertRaises(TypeError):
            builder.store(b, a)
        with self.assertRaises(TypeError):
            builder.load(b)
        # Mismatching pointer type
        with self.assertRaises(TypeError) as cm:
            builder.store(b, e)
        self.assertEqual(str(cm.exception),
                         "cannot store i32 to double*: mismatching types")
        self.check_block(block, """\
            my_block:
                %"c" = alloca i32
                %"d" = alloca i32, i32 42
                %"e" = alloca double, i32 %".1"
                store double %".3", double* %"e"
                store i32 %".2", i32* %"c"
                %"g" = load i32, i32* %"c"
                store i32 %".2", i32* %"c", align 1
                %"i" = load i32, i32* %"c", align 1
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
                %"d" = getelementptr i32*, i32** %"c", i32 5, i32 %".1"
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
                %"j" = load {i8, {i32, i1}}, {i8, {i32, i1}}* %"ptr"
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

    def test_cbranch_weights(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        bb_true = builder.function.append_basic_block(name='b_true')
        bb_false = builder.function.append_basic_block(name='b_false')
        br = builder.cbranch(ir.Constant(int1, False), bb_true, bb_false)
        br.set_weights([5, 42])
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                br i1 false, label %"b_true", label %"b_false", !prof !0
            """)
        self.check_metadata(builder.module, """\
            !0 = !{ !"branch_weights", i32 5, i32 42 }
            """)

    def test_branch_indirect(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        bb_1 = builder.function.append_basic_block(name='b_1')
        bb_2 = builder.function.append_basic_block(name='b_2')
        indirectbr = builder.branch_indirect(ir.BlockAddress(builder.function, bb_1))
        indirectbr.add_destination(bb_1)
        indirectbr.add_destination(bb_2)
        self.assertTrue(block.is_terminated)
        self.check_block(block, """\
            my_block:
                indirectbr i8* blockaddress(@"my_func", %"b_1"), [label %"b_1", label %"b_2"]
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
        # A plain Python value gets converted into the right IR constant
        sw.add_case(2, bb_ontwo)
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
        res_f_readonly = builder.call(f, (a, b), 'res_f_readonly')
        res_f_readonly.attributes.add('readonly')
        self.check_block(block, """\
            my_block:
                %"res_f" = call float (i32, i32) @"f"(i32 %".1", i32 %".2")
                %"res_g" = call double (i32, ...) @"g"(i32 %".2", i32 %".1")
                %"res_f_fast" = call fastcc float (i32, i32) @"f"(i32 %".1", i32 %".2")
                %"res_f_readonly" = call float (i32, i32) @"f"(i32 %".1", i32 %".2") readonly
            """)

    def test_invoke(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        tp_f = ir.FunctionType(flt, (int32, int32))
        f = ir.Function(builder.function.module, tp_f, 'f')
        bb_normal = builder.function.append_basic_block(name='normal')
        bb_unwind = builder.function.append_basic_block(name='unwind')
        builder.invoke(f, (a, b), bb_normal, bb_unwind, 'res_f')
        self.check_block(block, """\
            my_block:
                %"res_f" = invoke float (i32, i32) @"f"(i32 %".1", i32 %".2")
                    to label %"normal" unwind label %"unwind"
            """)

    def test_landingpad(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        lp = builder.landingpad(ir.LiteralStructType([int32, int8.as_pointer()]), 'lp')
        int_typeinfo = ir.GlobalVariable(builder.function.module, int8.as_pointer(), "_ZTIi")
        int_typeinfo.global_constant = True
        lp.add_clause(ir.CatchClause(int_typeinfo))
        lp.add_clause(ir.FilterClause(ir.Constant(ir.ArrayType(int_typeinfo.type, 1),
                                                  [int_typeinfo])))
        builder.resume(lp)
        self.check_block(block, """\
            my_block:
                %"lp" = landingpad {i32, i8*}
                    catch i8** @"_ZTIi"
                    filter [1 x i8**] [i8** @"_ZTIi"]
                resume {i32, i8*} %"lp"
            """)

    def test_assume(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        c = builder.icmp_signed('>', a, b, name='c')
        builder.assume(c)
        self.check_block(block, """\
            my_block:
                %"c" = icmp sgt i32 %".1", %".2"
                call void (i1) @"llvm.assume"(i1 %"c")
            """)


class TestBuilderMisc(TestBase):
    """
    Test various other features of the IRBuilder class.
    """

    def test_attributes(self):
        block = self.block(name='start')
        builder = ir.IRBuilder(block)
        self.assertIs(builder.function, block.parent)
        self.assertIsInstance(builder.function, ir.Function)
        self.assertIs(builder.module, block.parent.module)
        self.assertIsInstance(builder.module, ir.Module)

    def test_goto_block(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        a, b = builder.function.args[:2]
        builder.add(a, b, 'c')
        bb_new = builder.append_basic_block(name='foo')
        with builder.goto_block(bb_new):
            builder.fadd(a, b, 'd')
            with builder.goto_entry_block():
                builder.sub(a, b, 'e')
            builder.fsub(a, b, 'f')
            builder.branch(bb_new)
        builder.mul(a, b, 'g')
        with builder.goto_block(bb_new):
            builder.fmul(a, b, 'h')
        self.check_block(block, """\
            my_block:
                %"c" = add i32 %".1", %".2"
                %"e" = sub i32 %".1", %".2"
                %"g" = mul i32 %".1", %".2"
            """)
        self.check_block(bb_new, """\
            foo:
                %"d" = fadd i32 %".1", %".2"
                %"f" = fsub i32 %".1", %".2"
                %"h" = fmul i32 %".1", %".2"
                br label %"foo"
            """)

    def test_if_then(self):
        block = self.block(name='one')
        builder = ir.IRBuilder(block)
        z = ir.Constant(int1, 0)
        a = builder.add(z, z, 'a')
        with builder.if_then(a) as bbend:
            b = builder.add(z, z, 'b')
            # Block will be terminated implicitly
        self.assertIs(builder.block, bbend)
        c = builder.add(z, z, 'c')
        with builder.if_then(c):
            d = builder.add(z, z, 'd')
            builder.branch(block)
            # No implicit termination
        self.check_func_body(builder.function, """\
            one:
                %"a" = add i1 0, 0
                br i1 %"a", label %"one.if", label %"one.endif"
            one.if:
                %"b" = add i1 0, 0
                br label %"one.endif"
            one.endif:
                %"c" = add i1 0, 0
                br i1 %"c", label %"one.endif.if", label %"one.endif.endif"
            one.endif.if:
                %"d" = add i1 0, 0
                br label %"one"
            one.endif.endif:
            """)

    def test_if_then_nested(self):
        # Implicit termination in a nested if/then
        block = self.block(name='one')
        builder = ir.IRBuilder(block)
        z = ir.Constant(int1, 0)
        a = builder.add(z, z, 'a')
        with builder.if_then(a) as bbend:
            b = builder.add(z, z, 'b')
            with builder.if_then(b) as bbend:
                c = builder.add(z, z, 'c')
        builder.ret_void()
        self.check_func_body(builder.function, """\
            one:
                %"a" = add i1 0, 0
                br i1 %"a", label %"one.if", label %"one.endif"
            one.if:
                %"b" = add i1 0, 0
                br i1 %"b", label %"one.if.if", label %"one.if.endif"
            one.endif:
                ret void
            one.if.if:
                %"c" = add i1 0, 0
                br label %"one.if.endif"
            one.if.endif:
                br label %"one.endif"
            """)

    def test_if_then_likely(self):
        def check(likely):
            block = self.block(name='one')
            builder = ir.IRBuilder(block)
            z = ir.Constant(int1, 0)
            with builder.if_then(z, likely=likely):
                pass
            self.check_block(block, """\
                one:
                    br i1 0, label %"one.if", label %"one.endif", !prof !0
                """)
            return builder
        builder = check(True)
        self.check_metadata(builder.module, """\
            !0 = !{ !"branch_weights", i32 99, i32 1 }
            """)
        builder = check(False)
        self.check_metadata(builder.module, """\
            !0 = !{ !"branch_weights", i32 1, i32 99 }
            """)

    def test_if_else(self):
        block = self.block(name='one')
        builder = ir.IRBuilder(block)
        z = ir.Constant(int1, 0)
        a = builder.add(z, z, 'a')
        with builder.if_else(a) as (then, otherwise):
            with then:
                b = builder.add(z, z, 'b')
            with otherwise:
                c = builder.add(z, z, 'c')
            # Each block will be terminated implicitly
        with builder.if_else(a) as (then, otherwise):
            with then:
                builder.branch(block)
            with otherwise:
                builder.ret_void()
            # No implicit termination
        self.check_func_body(builder.function, """\
            one:
                %"a" = add i1 0, 0
                br i1 %"a", label %"one.if", label %"one.else"
            one.if:
                %"b" = add i1 0, 0
                br label %"one.endif"
            one.else:
                %"c" = add i1 0, 0
                br label %"one.endif"
            one.endif:
                br i1 %"a", label %"one.endif.if", label %"one.endif.else"
            one.endif.if:
                br label %"one"
            one.endif.else:
                ret void
            one.endif.endif:
            """)

    def test_if_else_likely(self):
        def check(likely):
            block = self.block(name='one')
            builder = ir.IRBuilder(block)
            z = ir.Constant(int1, 0)
            with builder.if_else(z, likely=likely) as (then, otherwise):
                with then:
                    builder.branch(block)
                with otherwise:
                    builder.ret_void()
            self.check_func_body(builder.function, """\
                one:
                    br i1 0, label %"one.if", label %"one.else", !prof !0
                one.if:
                    br label %"one"
                one.else:
                    ret void
                one.endif:
                """)
            return builder
        builder = check(True)
        self.check_metadata(builder.module, """\
            !0 = !{ !"branch_weights", i32 99, i32 1 }
            """)
        builder = check(False)
        self.check_metadata(builder.module, """\
            !0 = !{ !"branch_weights", i32 1, i32 99 }
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

    def test_metadata(self):
        block = self.block(name='my_block')
        builder = ir.IRBuilder(block)
        builder.debug_metadata = builder.module.add_metadata([])
        a = builder.alloca(ir.PointerType(int32), name='c')
        self.check_block(block, """\
            my_block:
                %"c" = alloca i32*, !dbg !0
            """)


class TestTypes(TestBase):

    def has_logical_equality(self, ty):
        while isinstance(ty, ir.PointerType):
            ty = ty.pointee
        return not isinstance(ty, ir.LabelType)

    def assorted_types(self):
        """
        A bunch of mutually unequal types
        """
        # Avoid polluting the namespace
        context = ir.Context()
        types = [
            ir.LabelType(), ir.VoidType(),
            ir.FunctionType(int1, (int8, int8)), ir.FunctionType(int1, (int8,)),
            ir.FunctionType(int1, (int8,), var_arg=True),
            ir.FunctionType(int8, (int8,)),
            int1, int8, int32, flt, dbl,
            ir.ArrayType(flt, 5), ir.ArrayType(dbl, 5), ir.ArrayType(dbl, 4),
            ir.LiteralStructType((int1, int8)), ir.LiteralStructType((int8, int1)),
            context.get_identified_type("MyType1"),
            context.get_identified_type("MyType2"),
            ]
        types += [ir.PointerType(tp) for tp in types
                  if not isinstance(tp, (ir.VoidType, ir.LabelType))]

        return types

    def test_pickling(self):
        types = self.assorted_types()
        for ty in types:
            data = pickle.dumps(ty, protocol=-1)
            newty = pickle.loads(data)
            self.assertIs(newty.__class__, ty.__class__)
            self.assertEqual(str(newty), str(ty))
            if self.has_logical_equality(ty):
                self.assertEqual(newty, ty)

    def test_comparisons(self):
        types = self.assorted_types()
        for a, b in itertools.product(types, types):
            if a is not b:
                self.assertFalse(a == b, (a, b))
                self.assertTrue(a != b, (a, b))
        # We assume copy.copy() works fine here...
        for tp in types:
            other = copy.copy(tp)
            if self.has_logical_equality(tp):
                self.assertTrue(tp == other, (tp, other))
                self.assertFalse(tp != other, (tp, other))
            else:
                self.assertFalse(tp == other, (tp, other))
                self.assertTrue(tp != other, (tp, other))

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
        self.assertEqual(str(mytype), "%\"MyType\"")
        mytype1 = context.get_identified_type("MyType\\")
        self.assertEqual(str(mytype1), "%\"MyType\\5c\"")
        mytype2 = context.get_identified_type("MyType\"")
        self.assertEqual(str(mytype2), "%\"MyType\\22\"")

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

        context = ir.Context()
        tp = ir.IdentifiedStructType(context, "MyType")
        tp.set_body(dbl, ir.LiteralStructType((int1, int8)))
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

    def test_abi_alignment(self):
        td = llvm.create_target_data("e-m:e-i64:64-f80:128-n8:16:32:64-S128")
        def check(tp, expected):
            self.assertIn(tp.get_abi_alignment(td), expected)
        check(int8, (1, 2, 4))
        check(int32, (4,))
        check(int64, (8,))
        check(ir.ArrayType(int8, 5), (1, 2, 4))
        check(ir.ArrayType(int32, 5), (4,))
        check(ir.LiteralStructType((dbl, flt, flt)), (8,))

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

    def test_target_data_non_default_context(self):
        context = ir.Context()
        mytype = context.get_identified_type("MyType")
        mytype.elements = [ir.IntType(32)]
        module = ir.Module(context=context)
        td = llvm.create_target_data("e-m:e-i64:64-f80:128-n8:16:32:64-S128")
        self.assertEqual(mytype.get_abi_size(td, context=context), 4)


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
        c = ir.Constant(int1, None)
        self.assertEqual(str(c), 'i1 0')

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
        c = ir.Constant(dbl, None)
        self.assertEqual(str(c), 'double 0.0')

    def test_arrays(self):
        c = ir.Constant(ir.ArrayType(int32, 3), (c32(5), c32(6), c32(4)))
        self.assertEqual(str(c), '[3 x i32] [i32 5, i32 6, i32 4]')
        c = ir.Constant(ir.ArrayType(int32, 2), (c32(5), c32(ir.Undefined)))
        self.assertEqual(str(c), '[2 x i32] [i32 5, i32 undef]')

        c = ir.Constant.literal_array((c32(5), c32(6), c32(ir.Undefined)))
        self.assertEqual(str(c), '[3 x i32] [i32 5, i32 6, i32 undef]')
        with self.assertRaises(TypeError) as raises:
            ir.Constant.literal_array((c32(5), ir.Constant(flt, 1.5)))
        self.assertEqual(str(raises.exception),
                         "all elements must have the same type")

        c = ir.Constant(ir.ArrayType(int32, 2), ir.Undefined)
        self.assertEqual(str(c), '[2 x i32] undef')
        c = ir.Constant(ir.ArrayType(int32, 2), None)
        self.assertEqual(str(c), '[2 x i32] zeroinitializer')
        # Raw array syntax
        c = ir.Constant(ir.ArrayType(int8, 11), bytearray(b"foobar_123\x80"))
        self.assertEqual(str(c), r'[11 x i8] c"foobar\5f123\80"')
        c = ir.Constant(ir.ArrayType(int8, 4), bytearray(b"\x00\x01\x04\xff"))
        self.assertEqual(str(c), r'[4 x i8] c"\00\01\04\ff"')
        # Recursive instantiation of inner constants
        c = ir.Constant(ir.ArrayType(int32, 3), (5, ir.Undefined, 6))
        self.assertEqual(str(c), '[3 x i32] [i32 5, i32 undef, i32 6]')
        # Invalid number of args
        with self.assertRaises(ValueError):
            ir.Constant(ir.ArrayType(int32, 3), (5, 6))

    def test_structs(self):
        st1 = ir.LiteralStructType((flt, int1))
        st2 = ir.LiteralStructType((int32, st1))
        c = ir.Constant(st1, (ir.Constant(ir.FloatType(), 1.5),
                              ir.Constant(int1, True)))
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c = ir.Constant.literal_struct((ir.Constant(ir.FloatType(), 1.5),
                                        ir.Constant(int1, True)))
        self.assertEqual(c.type, st1)
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c = ir.Constant.literal_struct((ir.Constant(ir.FloatType(), 1.5),
                                        ir.Constant(int1, ir.Undefined)))
        self.assertEqual(c.type, st1)
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 undef}')
        c = ir.Constant(st1, ir.Undefined)
        self.assertEqual(str(c), '{float, i1} undef')
        c = ir.Constant(st1, None)
        self.assertEqual(str(c), '{float, i1} zeroinitializer')
        # Recursive instantiation of inner constants
        c1 = ir.Constant(st1, (1.5, True))
        self.assertEqual(str(c1), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c2 = ir.Constant(st2, (42, c1))
        self.assertEqual(str(c2), '{i32, {float, i1}} '
                                  '{i32 42, {float, i1} {float 0x3ff8000000000000, i1 true}}')
        c3 = ir.Constant(st2, (42, (1.5, True)))
        self.assertEqual(str(c3), str(c2))
        # Invalid number of args
        with self.assertRaises(ValueError):
            ir.Constant(st2, (4, 5, 6))

    def test_type_instantiaton(self):
        """
        Instantiating a type should create a constant.
        """
        c = int8(42)
        self.assertIsInstance(c, ir.Constant)
        self.assertEqual(str(c), 'i8 42')
        c = int1(True)
        self.assertIsInstance(c, ir.Constant)
        self.assertEqual(str(c), 'i1 true')
        # Arrays
        at = ir.ArrayType(int32, 3)
        c = at([c32(4), c32(5), c32(6)])
        self.assertEqual(str(c), '[3 x i32] [i32 4, i32 5, i32 6]')
        c = at([4, 5, 6])
        self.assertEqual(str(c), '[3 x i32] [i32 4, i32 5, i32 6]')
        c = at(None)
        self.assertEqual(str(c), '[3 x i32] zeroinitializer')
        with self.assertRaises(ValueError):
            at([4, 5, 6, 7])
        # Structs
        st1 = ir.LiteralStructType((flt, int1))
        st2 = ir.LiteralStructType((int32, st1))
        c = st1((1.5, True))
        self.assertEqual(str(c), '{float, i1} {float 0x3ff8000000000000, i1 true}')
        c = st2((42, (1.5, True)))
        self.assertEqual(str(c), '{i32, {float, i1}} '
                                 '{i32 42, {float, i1} {float 0x3ff8000000000000, i1 true}}')

    def test_repr(self):
        """
        Constants should have a useful repr().
        """
        c = int32(42)
        self.assertEqual(repr(c), "<ir.Constant type='i32' value=42>")

    def test_encoding_problem(self):
        c = ir.Constant(ir.ArrayType(ir.IntType(8), 256),
                        bytearray(range(256)))
        m = self.module()
        gv = ir.GlobalVariable(m, c.type, "myconstant")
        gv.global_constant = True
        gv.initializer = c
        # With utf-8, the following will cause:
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe0 in position 136: invalid continuation byte
        parsed = llvm.parse_assembly(str(m))
        # Make sure the encoding does not modify the IR
        reparsed = llvm.parse_assembly(str(parsed))
        self.assertEqual(str(parsed), str(reparsed))

    def test_gep(self):
        m = self.module()
        tp = ir.LiteralStructType((flt, int1))
        gv = ir.GlobalVariable(m, tp, "myconstant")
        c = gv.gep([ir.Constant(int32, x) for x in (0, 1)])
        self.assertEqual(str(c),
            'getelementptr ({float, i1}, {float, i1}* @"myconstant", i32 0, i32 1)')
        self.assertEqual(c.type, ir.PointerType(int1))

    def test_bitcast(self):
        m = self.module()
        gv = ir.GlobalVariable(m, int32, "myconstant")
        c = gv.bitcast(int64.as_pointer())
        self.assertEqual(str(c), 'bitcast (i32* @"myconstant" to i64*)')

    def test_inttoptr(self):
        c = ir.Constant(int32, 0).inttoptr(int64.as_pointer())
        self.assertEqual(str(c), 'inttoptr (i32 0 to i64*)')


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
