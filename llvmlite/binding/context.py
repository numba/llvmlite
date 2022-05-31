from __future__ import annotations

from typing import Any

from llvmlite.binding import ffi


def create_context() -> ContextRef:
    return ContextRef(ffi.lib.LLVMPY_ContextCreate())  # type: ignore


def get_global_context() -> GlobalContextRef:
    return GlobalContextRef(ffi.lib.LLVMPY_GetGlobalContext())  # type: ignore


class ContextRef(ffi.ObjectRef):
    def __init__(self, context_ptr: Any) -> None:
        super().__init__(context_ptr)

    def _dispose(self) -> None:
        ffi.lib.LLVMPY_ContextDispose(self)  # type: ignore


class GlobalContextRef(ContextRef):
    def _dispose(self) -> None:
        pass


ffi.lib.LLVMPY_GetGlobalContext.restype = ffi.LLVMContextRef  # type: ignore

ffi.lib.LLVMPY_ContextCreate.restype = ffi.LLVMContextRef  # type: ignore

ffi.lib.LLVMPY_ContextDispose.argtypes = [ffi.LLVMContextRef]  # type: ignore
