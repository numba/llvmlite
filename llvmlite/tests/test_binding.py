
import ctypes
from ctypes import *
import unittest

from llvmlite import binding as llvm
from . import TestCase


asm_sum = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    @glob = global i32 0, align 4

    define i32 @sum(i32 %.1, i32 %.2) {{
      %.3 = add i32 %.1, %.2
      ret i32 %.3
    }}
    """

asm_mul = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    define i32 @mul(i32 %.1, i32 %.2) {{
      %.3 = mul i32 %.1, %.2
      ret i32 %.3
    }}
    """

# `fadd` used on integer inputs
asm_parse_error = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    define i32 @sum(i32 %.1, i32 %.2) {{
      %.3 = fadd i32 %.1, %.2
      ret i32 %.3
    }}
    """

# "%.bug" definition references itself
asm_verification_fail = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    define void @sum() {{
      %.bug = add i32 1, %.bug
      ret void
    }}
    """


class TestBindingFunctions(TestCase):

    def setUp(self):
        llvm.initialize()
        llvm.initialize_native_target()

    def _parse_assembly(self, asm):
        asm = asm.format(triple=llvm.get_default_triple())
        mod = llvm.parse_assembly(asm)
        mod.verify()
        return mod

    def test_parse_assembly(self):
        self._parse_assembly(asm_sum)

    def test_parse_assembly_error(self):
        with self.assertRaises(RuntimeError) as cm:
            self._parse_assembly(asm_parse_error)
        s = str(cm.exception)
        self.assertIn("parsing error", s)
        self.assertIn("invalid operand type", s)

    def test_mcjit(self):
        mod = self._parse_assembly(asm_sum)
        with llvm.create_mcjit_compiler(mod) as ee:
            ee.finalize_object()
            cfptr = ee.get_pointer_to_global(mod.get_function('sum'))

            cfunc = CFUNCTYPE(c_int, c_int, c_int)(cfptr)
            res = cfunc(2, -5)
            self.assertEqual(-3, res)


class TestModuleRef(TestCase):

    def module(self, asm=asm_sum):
        asm = asm.format(triple=llvm.get_default_triple())
        mod = llvm.parse_assembly(asm)
        return mod

    def test_str(self):
        mod = self.module()
        s = str(mod).strip()
        self.assertTrue(s.startswith('; ModuleID ='), s)

    def test_close(self):
        mod = self.module()
        str(mod)
        mod.close()
        with self.assertRaises(ctypes.ArgumentError):
            str(mod)
        mod.close()

    def test_with(self):
        mod = self.module()
        str(mod)
        with mod:
            str(mod)
        with self.assertRaises(ctypes.ArgumentError):
            str(mod)
        with mod:
            pass

    def test_data_layout(self):
        mod = self.module()
        s = mod.data_layout
        self.assertIsInstance(s, str)

    def test_verify(self):
        # Verify successful
        mod = self.module()
        self.assertIs(mod.verify(), None)
        # Verify failed
        mod = self.module(asm_verification_fail)
        with self.assertRaises(RuntimeError) as cm:
            mod.verify()
        s = str(cm.exception)
        self.assertIn("%.bug = add i32 1, %.bug", s)

    def test_get_function(self):
        mod = self.module()
        fn = mod.get_function("sum")
        self.assertIsInstance(fn, llvm.ValueRef)
        self.assertEqual(fn.name, "sum")

        with self.assertRaises(NameError):
            mod.get_function("foo")

    def test_get_global_variable(self):
        mod = self.module()
        gv = mod.get_global_variable("glob")
        self.assertIsInstance(gv, llvm.ValueRef)
        self.assertEqual(gv.name, "glob")

        with self.assertRaises(NameError):
            mod.get_global_variable("bar")

    def test_link_in(self):
        dest = self.module()
        src = self.module(asm_mul)
        dest.link_in(src)
        dest.get_function("mul")


if __name__ == "__main__":
    unittest.main()
