from __future__ import print_function, absolute_import

import platform
import re
from ctypes import CFUNCTYPE, c_int
import unittest
from . import TestCase
from llvmlite import ir
from llvmlite import binding as llvm

llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


@unittest.skipUnless(platform.system() in ["Linux", "Darwin"],
                     "test only works on Linux and Darwin")
class TestDebugInfo(TestCase):
    def check_debuginfo_in_assembly(self, asm):
        if platform.system() == "Linux":
            regex = re.compile("\.section\s+\.debug_info")
            self.assertTrue(regex.search(asm))
        elif platform.system() == "Darwin":
            self.assertIn("DWARF", asm)
            self.assertIn("showdebug.c", asm)
        else:
            self.fail("Unknown platform")

    def test_simple_debug_info(self):
        """
        Generator int foo(int) and have debug info match the signature
        """
        module = ir.Module()
        fnty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        foo = ir.Function(module, fnty, name="foo")

        builder = ir.IRBuilder(foo.append_basic_block())
        builder.ret(foo.args[0])

        di = ir.DIBuilder(module, "/tmp/showdebug.c")

        di.create_compile_unit()
        di_int = di.create_base_type("int", ir.DI_TypeKind.DW_ATE_signed, 32)
        di.add_subprogram(foo, "foo", di_int, [di_int], lineno=6,
                          lineno_scope=6)
        asm = str(module)

        regex = re.compile(r'i32\s+786478.*metadata\s\!"foo"')
        self.assertTrue(regex.search(asm))

        # Realize
        module = llvm.parse_assembly(asm)

        # If this fail, the debug info is removed by LLVM because it is
        # malformed
        self.assertTrue(regex.search(str(module)))

        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine(jitdebug=True, opt=0)
        engine = llvm.create_mcjit_compiler(module, tm)

        engine.finalize_object()

        addr = engine.get_pointer_to_function(module.get_function("foo"))
        prot = CFUNCTYPE(c_int, c_int)
        callme = prot(addr)

        arg = 0xdead
        self.assertEqual(arg, callme(arg))

        # Ensure debug info is generated in the assembly
        assembly = tm.emit_assembly(module)
        self.check_debuginfo_in_assembly(assembly)

    def test_minimal_debug_info(self):
        """
        Generator int foo(int) and the debug info does not contain
        return type and argument type.
        """
        module = ir.Module()
        fnty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
        foo = ir.Function(module, fnty, name="foo")

        builder = ir.IRBuilder(foo.append_basic_block())
        builder.ret(foo.args[0])

        di = ir.DIBuilder(module, "/tmp/showdebug.c")

        di.create_compile_unit()
        di.add_subprogram(foo, "foo")
        asm = str(module)

        regex = re.compile(r'i32\s+786478.*metadata\s\!"foo"')
        self.assertTrue(regex.search(asm))

        # Realize
        module = llvm.parse_assembly(asm)

        # If this fail, the debug info is removed by LLVM because it is
        # malformed
        self.assertTrue(regex.search(str(module)))

        target = llvm.Target.from_default_triple()
        tm = target.create_target_machine(jitdebug=True, opt=0)
        engine = llvm.create_mcjit_compiler(module, tm)

        engine.finalize_object()

        addr = engine.get_pointer_to_function(module.get_function("foo"))
        prot = CFUNCTYPE(c_int, c_int)
        callme = prot(addr)

        arg = 0xdead
        self.assertEqual(arg, callme(arg))

        # Ensure debug info is generated in the assembly
        assembly = tm.emit_assembly(module)
        self.check_debuginfo_in_assembly(assembly)


if __name__ == '__main__':
    unittest.main()
