from . import TestCase

from llvmlite import binding as llvm
from llvmlite.binding import dylib
import platform
from ctypes.util import find_library
import unittest

@unittest.skipUnless(platform.system() in ["Linux", "Darwin"], "Unsupport test for current OS")
class TestDylib(TestCase):
    def setUp(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        self.system = platform.system()

    def test_bad_library(self):
        with self.assertRaises(Exception) as context:
            dylib.load_library_permanently("zzzasdkf;jasd;l")
        if self.system  == "Linux":
            self.assertTrue('zzzasdkf;jasd;l: cannot open shared object file: No such file or directory'
                            in str(context.exception))
        elif self.system == "Darwin":
            self.assertTrue('dlopen(zzzasdkf;jasd;l, 9): image not found'
                            in str(context.exception))

    def test_libm(self):
        try:
            if self.system  == "Linux":
                libm = find_library("m")
            elif self.system == "Darwin":
                libm = find_library("libm")
            dylib.load_library_permanently(libm)
        except Exception:
            self.fail("Valid call to link library should not fail.")
