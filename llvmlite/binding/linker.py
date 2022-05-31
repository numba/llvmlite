from __future__ import annotations

from ctypes import POINTER, c_char_p, c_int
from typing import TYPE_CHECKING

from llvmlite.binding import ffi

if TYPE_CHECKING:
    from llvmlite.binding.module import ModuleRef


def link_modules(dst: ModuleRef, src: ModuleRef) -> None:
    with ffi.OutputString() as outerr:
        err = ffi.lib.LLVMPY_LinkModules(dst, src, outerr)
        # The underlying module was destroyed
        src.detach()
        if err:
            raise RuntimeError(str(outerr))


ffi.lib.LLVMPY_LinkModules.argtypes = [
    ffi.LLVMModuleRef,
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_LinkModules.restype = c_int
