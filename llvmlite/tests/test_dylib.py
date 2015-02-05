import unittest
from . import TestCase

from llvmlite import binding as llvm
from llvmlite.binding import dylib
import platform


class TestDylib(TestCase):

    def setUp(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def test_bad_library(self):
        with self.assertRaises(Exception) as context:
            dylib.load_library_permanently("zzzasdkf;jasd;l")
        system = platform.system()
        if system  == "Linux":
            self.assertTrue('zzzasdkf;jasd;l: cannot open shared object file: No such file or directory'
                            in str(context.exception))
        elif system == "Darwin":
            self.assertTrue('dlopen(zzzasdkf;jasd;l, 9): image not found'
                            in str(context.exception))
