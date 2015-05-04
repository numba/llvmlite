from __future__ import print_function, absolute_import

import ctypes
from ctypes import *
from ctypes.util import find_library
import subprocess
import sys
import unittest
import platform

from llvmlite import six
from llvmlite import binding as llvm
from llvmlite.binding import ffi
from . import TestCase


asm_sum = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    @glob = global i32 0
    @glob_b = global i8 0
    @glob_f = global float 1.5
    @glob_struct = global {{ i64, [2 x i64]}} {{i64 0, [2 x i64] [i64 0, i64 0]}}

    define i32 @sum(i32 %.1, i32 %.2) {{
      %.3 = add i32 %.1, %.2
      %.4 = add i32 0, %.3
      ret i32 %.4
    }}
    """

asm_sum2 = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

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

asm_sum_declare = r"""
    ; ModuleID = '<string>'
    target triple = "{triple}"

    declare i32 @sum(i32 %.1, i32 %.2)
    """

class BaseTest(TestCase):

    def setUp(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def module(self, asm=asm_sum):
        asm = asm.format(triple=llvm.get_default_triple())
        mod = llvm.parse_assembly(asm)
        return mod

    def glob(self, name='glob', mod=None):
        if mod is None:
            mod = self.module()
        return mod.get_global_variable(name)

    def target_machine(self):
        target = llvm.Target.from_default_triple()
        return target.create_target_machine()


class TestMisc(BaseTest):
    """
    Test miscellaneous functions in llvm.binding.
    """

    def test_parse_assembly(self):
        self.module(asm_sum)

    def test_parse_assembly_error(self):
        with self.assertRaises(RuntimeError) as cm:
            self.module(asm_parse_error)
        s = str(cm.exception)
        self.assertIn("parsing error", s)
        self.assertIn("invalid operand type", s)

    def test_dylib_symbols(self):
        llvm.add_symbol("__xyzzy", 1234)
        llvm.add_symbol("__xyzzy", 5678)
        addr = llvm.address_of_symbol("__xyzzy")
        self.assertEqual(addr, 5678)
        addr = llvm.address_of_symbol("__foobar")
        self.assertIs(addr, None)

    def test_get_default_triple(self):
        triple = llvm.get_default_triple()
        self.assertIsInstance(triple, str)
        self.assertTrue(triple)

    def test_get_host_cpu_name(self):
        cpu = llvm.get_host_cpu_name()
        self.assertIsInstance(cpu, str)
        self.assertTrue(cpu)

    def test_initfini(self):
        code = """if 1:
            from llvmlite import binding as llvm

            llvm.initialize()
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            llvm.shutdown()
            """
        subprocess.check_call([sys.executable, "-c", code])

    def test_set_option(self):
        # We cannot set an option multiple times (LLVM would exit() the
        # process), so run the code in a subprocess.
        code = """if 1:
            from llvmlite import binding as llvm

            llvm.set_option("progname", "-debug-pass=Disabled")
            """
        subprocess.check_call([sys.executable, "-c", code])

    def test_version(self):
        self.assertIn(llvm.llvm_version_info,
                      [(3, 5, 0), (3, 5, 1)])


class TestModuleRef(BaseTest):

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
        with self.assertRaises(RuntimeError):
            with mod:
                pass

    def test_data_layout(self):
        mod = self.module()
        s = mod.data_layout
        self.assertIsInstance(s, str)
        mod.data_layout = s
        self.assertEqual(s, mod.data_layout)

    def test_triple(self):
        mod = self.module()
        s = mod.triple
        self.assertEqual(s, llvm.get_default_triple())
        mod.triple = ''
        self.assertEqual(mod.triple, '')

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

        # Check that fn keeps the module instance alive
        del mod
        str(fn.module)

    def test_get_global_variable(self):
        mod = self.module()
        gv = mod.get_global_variable("glob")
        self.assertIsInstance(gv, llvm.ValueRef)
        self.assertEqual(gv.name, "glob")

        with self.assertRaises(NameError):
            mod.get_global_variable("bar")

        # Check that gv keeps the module instance alive
        del mod
        str(gv.module)

    def test_global_variables(self):
        mod = self.module()
        it = mod.global_variables
        del mod
        globs = sorted(it, key=lambda value: value.name)
        self.assertEqual(len(globs), 4)
        self.assertEqual([g.name for g in globs],
                         ["glob", "glob_b", "glob_f", "glob_struct"])

    def test_functions(self):
        mod = self.module()
        it = mod.functions
        del mod
        funcs = list(it)
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0].name, "sum")

    def test_link_in(self):
        dest = self.module()
        src = self.module(asm_mul)
        dest.link_in(src)
        self.assertEqual(sorted(f.name for f in dest.functions), ["mul", "sum"])
        dest.get_function("mul")
        dest.close()
        with self.assertRaises(ctypes.ArgumentError):
            src.get_function("mul")

    def test_link_in_preserve(self):
        dest = self.module()
        src2 = self.module(asm_mul)
        dest.link_in(src2, preserve=True)
        self.assertEqual(sorted(f.name for f in dest.functions), ["mul", "sum"])
        dest.close()
        src2.get_function("mul")

    def test_link_in_error(self):
        # Raise an error by trying to link two modules with the same global
        # definition "sum".
        dest = self.module()
        src = self.module(asm_sum2)
        with self.assertRaises(RuntimeError) as cm:
            dest.link_in(src)
        self.assertIn("symbol multiply defined", str(cm.exception))

    def test_as_bitcode(self):
        mod = self.module()
        bc = mod.as_bitcode()
        # Refer to http://llvm.org/docs/doxygen/html/ReaderWriter_8h_source.html#l00064
        # and http://llvm.org/docs/doxygen/html/ReaderWriter_8h_source.html#l00092
        bitcode_wrapper_magic = b'\xde\xc0\x17\x0b'
        bitcode_magic = b'BC'
        self.assertTrue(bc.startswith(bitcode_magic) or
                        bc.startswith(bitcode_wrapper_magic))

    def test_parse_bitcode_error(self):
        with self.assertRaises(RuntimeError) as cm:
            llvm.parse_bitcode(b"")
        self.assertIn("LLVM bitcode parsing error", str(cm.exception))
        self.assertIn("Invalid bitcode signature", str(cm.exception))

    def test_bitcode_roundtrip(self):
        bc = self.module().as_bitcode()
        mod = llvm.parse_bitcode(bc)
        self.assertEqual(mod.as_bitcode(), bc)
        mod.get_function("sum")
        mod.get_global_variable("glob")

    def test_cloning(self):
        m = self.module()
        cloned = m.clone()
        self.assertIsNot(cloned, m)
        self.assertEqual(cloned.as_bitcode(), m.as_bitcode())


class JITTestMixin(object):
    """
    Mixin for ExecutionEngine tests.
    """

    def test_run_code(self):
        mod = self.module()
        with self.jit(mod) as ee:
            ee.finalize_object()
            cfptr = ee.get_pointer_to_global(mod.get_function('sum'))

            cfunc = CFUNCTYPE(c_int, c_int, c_int)(cfptr)
            res = cfunc(2, -5)
            self.assertEqual(-3, res)

    def test_close(self):
        ee = self.jit(self.module())
        ee.close()
        ee.close()
        with self.assertRaises(ctypes.ArgumentError):
            ee.finalize_object()

    def test_with(self):
        ee = self.jit(self.module())
        with ee:
            pass
        with self.assertRaises(RuntimeError):
            with ee:
                pass
        with self.assertRaises(ctypes.ArgumentError):
            ee.finalize_object()

    def test_module_lifetime(self):
        mod = self.module()
        ee = self.jit(mod)
        ee.close()
        mod.close()

    def test_module_lifetime2(self):
        mod = self.module()
        ee = self.jit(mod)
        mod.close()
        ee.close()

    def test_add_module(self):
        ee = self.jit(self.module())
        mod = self.module(asm_mul)
        ee.add_module(mod)
        with self.assertRaises(KeyError):
            ee.add_module(mod)
        self.assertFalse(mod.closed)
        ee.close()
        self.assertTrue(mod.closed)

    def test_add_module_lifetime(self):
        ee = self.jit(self.module())
        mod = self.module(asm_mul)
        ee.add_module(mod)
        mod.close()
        ee.close()

    def test_add_module_lifetime2(self):
        ee = self.jit(self.module())
        mod = self.module(asm_mul)
        ee.add_module(mod)
        ee.close()
        mod.close()

    def test_remove_module(self):
        ee = self.jit(self.module())
        mod = self.module(asm_mul)
        ee.add_module(mod)
        ee.remove_module(mod)
        with self.assertRaises(KeyError):
            ee.remove_module(mod)
        self.assertFalse(mod.closed)
        ee.close()
        self.assertFalse(mod.closed)

    def test_target_data(self):
        mod = self.module()
        ee = self.jit(mod)
        td = ee.target_data
        # A singleton is returned
        self.assertIs(ee.target_data, td)
        str(td)
        del mod, ee
        str(td)

    def test_target_data_abi_enquiries(self):
        mod = self.module()
        ee = self.jit(mod)
        td = ee.target_data
        gv_i32 = mod.get_global_variable("glob")
        gv_i8 = mod.get_global_variable("glob_b")
        gv_struct = mod.get_global_variable("glob_struct")
        # A global is a pointer, it has the ABI size of a pointer
        pointer_size = 4 if sys.maxsize < 2 ** 32 else 8
        for g in (gv_i32, gv_i8, gv_struct):
            self.assertEqual(td.get_abi_size(g.type), pointer_size)

        self.assertEqual(td.get_pointee_abi_size(gv_i32.type), 4)
        self.assertEqual(td.get_pointee_abi_alignment(gv_i32.type), 4)

        self.assertEqual(td.get_pointee_abi_size(gv_i8.type), 1)
        self.assertIn(td.get_pointee_abi_alignment(gv_i8.type), (1, 2, 4))

        self.assertEqual(td.get_pointee_abi_size(gv_struct.type), 24)
        self.assertIn(td.get_pointee_abi_alignment(gv_struct.type), (4, 8))


class JITWithTMTestMixin(JITTestMixin):

    def test_emit_assembly(self):
        """Test TargetMachineRef.emit_assembly()"""
        target_machine = self.target_machine()
        mod = self.module()
        ee = self.jit(mod, target_machine)
        raw_asm = target_machine.emit_assembly(mod)
        self.assertIn("sum", raw_asm)

    def test_emit_object(self):
        """Test TargetMachineRef.emit_object()"""
        target_machine = self.target_machine()
        mod = self.module()
        ee = self.jit(mod, target_machine)
        code_object = target_machine.emit_object(mod)
        self.assertIsInstance(code_object, six.binary_type)
        if sys.platform.startswith('linux'):
            # Sanity check
            self.assertIn(b"ELF", code_object[:10])


class TestMCJit(BaseTest, JITWithTMTestMixin):
    """
    Test JIT engines created with create_mcjit_compiler().
    """

    def jit(self, mod, target_machine=None):
        if target_machine is None:
            target_machine = self.target_machine()
        return llvm.create_mcjit_compiler(mod, target_machine)


class TestLegacyJitWithTM(BaseTest, JITWithTMTestMixin):
    """
    Test JIT engines created with create_jit_compiler_with_tm().
    """

    def jit(self, mod, target_machine=None):
        if target_machine is None:
            target_machine = self.target_machine()
        return llvm.create_jit_compiler_with_tm(mod, target_machine)


class TestLegacyJit(BaseTest, JITTestMixin):
    """
    Test JIT engines created with create_jit_compiler().
    """

    def jit(self, mod):
        return llvm.create_jit_compiler(mod)


class TestValueRef(BaseTest):

    def test_str(self):
        mod = self.module()
        glob = mod.get_global_variable("glob")
        self.assertEqual(str(glob), "@glob = global i32 0")

    def test_name(self):
        mod = self.module()
        glob = mod.get_global_variable("glob")
        self.assertEqual(glob.name, "glob")
        glob.name = "foobar"
        self.assertEqual(glob.name, "foobar")

    def test_linkage(self):
        mod = self.module()
        glob = mod.get_global_variable("glob")
        linkage = glob.linkage
        self.assertIsInstance(glob.linkage, llvm.Linkage)
        glob.linkage = linkage
        self.assertEqual(glob.linkage, linkage)
        for linkage in ("internal", "external"):
            glob.linkage = linkage
            self.assertIsInstance(glob.linkage, llvm.Linkage)
            self.assertEqual(glob.linkage.name, linkage)

    def test_add_function_attribute(self):
        mod = self.module()
        fn = mod.get_function("sum")
        fn.add_function_attribute("zext")

    def test_module(self):
        mod = self.module()
        glob = mod.get_global_variable("glob")
        self.assertIs(glob.module, mod)

    def test_type(self):
        mod = self.module()
        glob = mod.get_global_variable("glob")
        tp = glob.type
        self.assertIsInstance(tp, ffi.LLVMTypeRef)

    def test_close(self):
        glob = self.glob()
        glob.close()
        glob.close()

    def test_is_declaration(self):
        defined = self.module().get_function('sum')
        declared = self.module(asm_sum_declare).get_function('sum')
        self.assertFalse(defined.is_declaration)
        self.assertTrue(declared.is_declaration)


class TestTarget(BaseTest):

    def test_from_triple(self):
        f = llvm.Target.from_triple
        with self.assertRaises(RuntimeError) as cm:
            f("foobar")
        self.assertIn("No available targets are compatible with this triple",
                      str(cm.exception))
        triple = llvm.get_default_triple()
        target = f(triple)
        self.assertEqual(target.triple, triple)
        target.close()

    def test_create_target_machine(self):
        target = llvm.Target.from_triple(llvm.get_default_triple())
        # With the default settings
        target.create_target_machine('', '', 1, 'default', 'default')
        # With the host's CPU
        cpu = llvm.get_host_cpu_name()
        target.create_target_machine(cpu, '', 1, 'default', 'default')

    def test_name(self):
        t = llvm.Target.from_triple(llvm.get_default_triple())
        u = llvm.Target.from_default_triple()
        self.assertIsInstance(t.name, str)
        self.assertEqual(t.name, u.name)

    def test_description(self):
        t = llvm.Target.from_triple(llvm.get_default_triple())
        u = llvm.Target.from_default_triple()
        self.assertIsInstance(t.description, str)
        self.assertEqual(t.description, u.description)

    def test_str(self):
        target = llvm.Target.from_triple(llvm.get_default_triple())
        s = str(target)
        self.assertIn(target.name, s)
        self.assertIn(target.description, s)


class TestTargetData(BaseTest):

    def target_data(self):
        return llvm.create_target_data("e-m:e-i64:64-f80:128-n8:16:32:64-S128")

    def test_get_abi_size(self):
        td = self.target_data()
        glob = self.glob()
        self.assertEqual(td.get_abi_size(glob.type), 8)

    def test_add_pass(self):
        td = self.target_data()
        pm = llvm.create_module_pass_manager()
        td.add_pass(pm)


class TestTargetMachine(BaseTest):

    def test_add_analysis_passes(self):
        tm = self.target_machine()
        pm = llvm.create_module_pass_manager()
        tm.add_analysis_passes(pm)

    def test_target_data_from_tm(self):
        tm = self.target_machine()
        td = tm.target_data
        mod = self.module()
        gv_i32 = mod.get_global_variable("glob")
        # A global is a pointer, it has the ABI size of a pointer
        pointer_size = 4 if sys.maxsize < 2 ** 32 else 8
        self.assertEqual(td.get_abi_size(gv_i32.type), pointer_size)


class TestTargetLibraryInfo(BaseTest):

    def tli(self):
        return llvm.create_target_library_info(llvm.get_default_triple())

    def test_create_target_library_info(self):
        tli = llvm.create_target_library_info(llvm.get_default_triple())
        with tli:
            pass
        tli.close()

    def test_get_libfunc(self):
        tli = self.tli()
        with self.assertRaises(NameError):
            tli.get_libfunc("xyzzy")
        fmin = tli.get_libfunc("fmin")
        self.assertEqual(fmin.name, "fmin")
        self.assertIsInstance(fmin.identity, int)
        fmax = tli.get_libfunc("fmax")
        self.assertNotEqual(fmax.identity, fmin.identity)

    def test_set_unavailable(self):
        tli = self.tli()
        fmin = tli.get_libfunc("fmin")
        tli.set_unavailable(fmin)

    def test_disable_all(self):
        tli = self.tli()
        tli.disable_all()

    def test_add_pass(self):
        tli = self.tli()
        pm = llvm.create_module_pass_manager()
        tli.add_pass(pm)


class TestPassManagerBuilder(BaseTest):

    def pmb(self):
        return llvm.PassManagerBuilder()

    def test_old_api(self):
        # Test the create_pass_manager_builder() factory function
        pmb = llvm.create_pass_manager_builder()
        pmb.inlining_threshold = 2
        pmb.opt_level = 3

    def test_close(self):
        pmb = self.pmb()
        pmb.close()
        pmb.close()

    def test_opt_level(self):
        pmb = self.pmb()
        self.assertIsInstance(pmb.opt_level, six.integer_types)
        for i in range(4):
            pmb.opt_level = i
            self.assertEqual(pmb.opt_level, i)

    def test_size_level(self):
        pmb = self.pmb()
        self.assertIsInstance(pmb.size_level, six.integer_types)
        for i in range(4):
            pmb.size_level = i
            self.assertEqual(pmb.size_level, i)

    def test_inlining_threshold(self):
        pmb = self.pmb()
        with self.assertRaises(NotImplementedError):
            pmb.inlining_threshold
        for i in (25, 80, 350):
            pmb.inlining_threshold = i

    def test_disable_unit_at_a_time(self):
        pmb = self.pmb()
        self.assertIsInstance(pmb.disable_unit_at_a_time, bool)
        for b in (True, False):
            pmb.disable_unit_at_a_time = b
            self.assertEqual(pmb.disable_unit_at_a_time, b)

    def test_disable_unroll_loops(self):
        pmb = self.pmb()
        self.assertIsInstance(pmb.disable_unroll_loops, bool)
        for b in (True, False):
            pmb.disable_unroll_loops = b
            self.assertEqual(pmb.disable_unroll_loops, b)

    def test_populate_module_pass_manager(self):
        pmb = self.pmb()
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        pmb.close()
        pm.close()

    def test_populate_function_pass_manager(self):
        mod = self.module()
        pmb = self.pmb()
        pm = llvm.create_function_pass_manager(mod)
        pmb.populate(pm)
        pmb.close()
        pm.close()


class PassManagerTestMixin(object):

    def pmb(self):
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = 2
        return pmb

    def test_close(self):
        pm = self.pm()
        pm.close()
        pm.close()


class TestModulePassManager(BaseTest, PassManagerTestMixin):

    def pm(self):
        return llvm.create_module_pass_manager()

    def test_run(self):
        pm = self.pm()
        self.pmb().populate(pm)
        mod = self.module()
        orig_asm = str(mod)
        pm.run(mod)
        opt_asm = str(mod)
        # Quick check that optimizations were run
        self.assertIn("%.3", orig_asm)
        self.assertNotIn("%.3", opt_asm)


class TestFunctionPassManager(BaseTest, PassManagerTestMixin):

    def pm(self, mod=None):
        mod = mod or self.module()
        return llvm.create_function_pass_manager(mod)

    def test_initfini(self):
        pm = self.pm()
        pm.initialize()
        pm.finalize()

    def test_run(self):
        mod = self.module()
        fn = mod.get_function("sum")
        pm = self.pm(mod)
        self.pmb().populate(pm)
        mod.close()
        orig_asm = str(fn)
        pm.initialize()
        pm.run(fn)
        pm.finalize()
        opt_asm = str(fn)
        # Quick check that optimizations were run
        self.assertIn("%.4", orig_asm)
        self.assertNotIn("%.4", opt_asm)


class TestDylib(BaseTest):

    def test_bad_library(self):
        with self.assertRaises(RuntimeError):
            llvm.load_library_permanently("zzzasdkf;jasd;l")

    @unittest.skipUnless(platform.system() in ["Linux", "Darwin"], 
                         "test only works on Linux and Darwin")
    def test_libm(self):
        system = platform.system()
        if system == "Linux":
            libm = find_library("m")
        elif system == "Darwin":
            libm = find_library("libm")
        llvm.load_library_permanently(libm)


if __name__ == "__main__":
    unittest.main()
