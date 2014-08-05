from . import ffi


class ValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value.
    """

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)
