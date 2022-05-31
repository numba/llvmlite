from __future__ import annotations

from ctypes import (
    POINTER,
    byref,
    c_bool,
    c_char_p,
    c_size_t,
    create_string_buffer,
    string_at,
)
from typing import Any

from llvmlite.binding import ffi
from llvmlite.binding.common import _decode_string, _encode_string
from llvmlite.binding.context import GlobalContextRef, get_global_context
from llvmlite.binding.linker import link_modules
from llvmlite.binding.value import TypeRef, ValueRef


def parse_assembly(llvmir: str, context: GlobalContextRef | None = None) -> ModuleRef:
    """
    Create Module from a LLVM IR string
    """
    if context is None:
        context = get_global_context()
    strbuf = c_char_p(_encode_string(llvmir))
    with ffi.OutputString() as errmsg:
        mod = ModuleRef(
            ffi.lib.LLVMPY_ParseAssembly(context, strbuf, errmsg),  # type: ignore
            context,
        )
        if errmsg:
            mod.close()
            raise RuntimeError("LLVM IR parsing error\n{0}".format(errmsg))
    return mod


def parse_bitcode(bitcode: bytes, context: GlobalContextRef | None = None) -> ModuleRef:
    """
    Create Module from a LLVM *bitcode* (a bytes object).
    """
    if context is None:
        context = get_global_context()
    buf = c_char_p(bitcode)
    bufsize = len(bitcode)
    with ffi.OutputString() as errmsg:
        mod = ModuleRef(
            ffi.lib.LLVMPY_ParseBitcode(context, buf, bufsize, errmsg),  # type: ignore
            context,
        )
        if errmsg:
            mod.close()
            raise RuntimeError("LLVM bitcode parsing error\n{0}".format(errmsg))
    return mod


class ModuleRef(ffi.ObjectRef):
    """
    A reference to a LLVM module.
    """

    def __init__(self, module_ptr: Any, context: GlobalContextRef) -> None:
        super().__init__(module_ptr)
        self._context = context

    def __str__(self) -> str:
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintModuleToString(self, outstr)  # type: ignore
            return str(outstr)

    def as_bitcode(self) -> bytes:
        """
        Return the module's LLVM bitcode, as a bytes object.
        """
        ptr = c_char_p(None)
        size = c_size_t(-1)
        ffi.lib.LLVMPY_WriteBitcodeToString(self, byref(ptr), byref(size))  # type: ignore
        if not ptr:
            raise MemoryError
        try:
            assert size.value >= 0
            return string_at(ptr, size.value)
        finally:
            ffi.lib.LLVMPY_DisposeString(ptr)  # type: ignore

    def _dispose(self) -> None:
        self._capi.LLVMPY_DisposeModule(self)  # type: ignore

    def get_function(self, name: str) -> ValueRef:
        """
        Get a ValueRef pointing to the function named *name*.
        NameError is raised if the symbol isn't found.
        """
        p = ffi.lib.LLVMPY_GetNamedFunction(self, _encode_string(name))  # type: ignore
        if not p:
            raise NameError(name)
        return ValueRef(p, "function", dict(module=self))

    def get_global_variable(self, name: str) -> ValueRef:
        """
        Get a ValueRef pointing to the global variable named *name*.
        NameError is raised if the symbol isn't found.
        """
        p = ffi.lib.LLVMPY_GetNamedGlobalVariable(self, _encode_string(name))  # type: ignore
        if not p:
            raise NameError(name)
        return ValueRef(p, "global", dict(module=self))

    def get_struct_type(self, name: str) -> TypeRef:
        """
        Get a TypeRef pointing to a structure type named *name*.
        NameError is raised if the struct type isn't found.
        """
        p = ffi.lib.LLVMPY_GetNamedStructType(self, _encode_string(name))  # type: ignore
        if not p:
            raise NameError(name)
        return TypeRef(p)

    def verify(self) -> None:
        """
        Verify the module IR's correctness.  RuntimeError is raised on error.
        """
        with ffi.OutputString() as outmsg:
            if ffi.lib.LLVMPY_VerifyModule(self, outmsg):  # type: ignore
                raise RuntimeError(str(outmsg))

    @property
    def name(self) -> str:
        """
        The module's identifier.
        """
        return _decode_string(ffi.lib.LLVMPY_GetModuleName(self))  # type: ignore

    @name.setter
    def name(self, value: str) -> None:
        ffi.lib.LLVMPY_SetModuleName(self, _encode_string(value))  # type: ignore

    @property
    def source_file(self) -> str:
        """
        The module's original source file name
        """
        return _decode_string(ffi.lib.LLVMPY_GetModuleSourceFileName(self))  # type: ignore

    @property
    def data_layout(self) -> str:
        """
        This module's data layout specification, as a string.
        """
        # LLVMGetDataLayout() points inside a std::string managed by LLVM.
        with ffi.OutputString(owned=False) as outmsg:
            ffi.lib.LLVMPY_GetDataLayout(self, outmsg)  # type: ignore
            return str(outmsg)

    @data_layout.setter
    def data_layout(self, strrep: str) -> None:
        ffi.lib.LLVMPY_SetDataLayout(self, create_string_buffer(strrep.encode("utf8")))  # type: ignore

    @property
    def triple(self) -> str:
        """
        This module's target "triple" specification, as a string.
        """
        # LLVMGetTarget() points inside a std::string managed by LLVM.
        with ffi.OutputString(owned=False) as outmsg:
            ffi.lib.LLVMPY_GetTarget(self, outmsg)  # type: ignore
            return str(outmsg)

    @triple.setter
    def triple(self, strrep: str) -> None:
        ffi.lib.LLVMPY_SetTarget(self, create_string_buffer(strrep.encode("utf8")))  # type: ignore

    def link_in(self, other: ModuleRef, preserve: bool = False) -> None:
        """
        Link the *other* module into this one.  The *other* module will
        be destroyed unless *preserve* is true.
        """
        if preserve:
            other = other.clone()
        link_modules(self, other)

    @property
    def global_variables(self) -> _GlobalsIterator:
        """
        Return an iterator over this module's global variables.
        The iterator will yield a ValueRef for each global variable.

        Note that global variables don't include functions
        (a function is a "global value" but not a "global variable" in
         LLVM parlance)
        """
        it = ffi.lib.LLVMPY_ModuleGlobalsIter(self)  # type: ignore
        return _GlobalsIterator(it, dict(module=self))  # type: ignore

    @property
    def functions(self) -> _FunctionsIterator:
        """
        Return an iterator over this module's functions.
        The iterator will yield a ValueRef for each function.
        """
        it = ffi.lib.LLVMPY_ModuleFunctionsIter(self)  # type: ignore
        return _FunctionsIterator(it, dict(module=self))  # type: ignore

    @property
    def struct_types(self) -> _TypesIterator:
        """
        Return an iterator over the struct types defined in
        the module. The iterator will yield a TypeRef.
        """
        it = ffi.lib.LLVMPY_ModuleTypesIter(self)  # type: ignore
        return _TypesIterator(it, dict(module=self))

    def clone(self) -> ModuleRef:
        return ModuleRef(ffi.lib.LLVMPY_CloneModule(self), self._context)  # type: ignore


class _Iterator(ffi.ObjectRef):

    kind: str | None = None

    def __init__(self, ptr: Any, parents: dict[str, ModuleRef]) -> None:
        ffi.ObjectRef.__init__(self, ptr)
        self._parents = parents
        assert self.kind is not None

    def __next__(self) -> ValueRef:
        vp = self._next()  # type: ignore
        if vp:
            # FIXME: self.kind can be None
            return ValueRef(vp, self.kind, self._parents)  # type: ignore
        else:
            raise StopIteration

    next = __next__

    def __iter__(self) -> _Iterator:
        return self


class _GlobalsIterator(_Iterator):

    kind = "global"

    def _dispose(self) -> None:
        self._capi.LLVMPY_DisposeGlobalsIter(self)  # type: ignore

    def _next(self) -> Any:
        return ffi.lib.LLVMPY_GlobalsIterNext(self)  # type: ignore


class _FunctionsIterator(_Iterator):

    kind = "function"

    def _dispose(self) -> None:
        self._capi.LLVMPY_DisposeFunctionsIter(self)  # type: ignore

    def _next(self) -> Any:
        return ffi.lib.LLVMPY_FunctionsIterNext(self)  # type: ignore


class _TypesIterator(_Iterator):

    kind = "type"

    def _dispose(self) -> None:
        self._capi.LLVMPY_DisposeTypesIter(self)  # type: ignore

    def __next__(self) -> TypeRef:  # type: ignore
        vp = self._next()
        if vp:
            return TypeRef(vp)
        else:
            raise StopIteration

    def _next(self) -> Any:
        return ffi.lib.LLVMPY_TypesIterNext(self)  # type: ignore

    next = __next__  # type: ignore


# =============================================================================
# Set function FFI

ffi.lib.LLVMPY_ParseAssembly.argtypes = [  # type: ignore
    ffi.LLVMContextRef,
    c_char_p,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_ParseAssembly.restype = ffi.LLVMModuleRef  # type: ignore

ffi.lib.LLVMPY_ParseBitcode.argtypes = [  # type: ignore
    ffi.LLVMContextRef,
    c_char_p,
    c_size_t,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_ParseBitcode.restype = ffi.LLVMModuleRef  # type: ignore

ffi.lib.LLVMPY_DisposeModule.argtypes = [ffi.LLVMModuleRef]  # type: ignore

ffi.lib.LLVMPY_PrintModuleToString.argtypes = [  # type: ignore
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_WriteBitcodeToString.argtypes = [  # type: ignore
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
    POINTER(c_size_t),
]

ffi.lib.LLVMPY_GetNamedFunction.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore
ffi.lib.LLVMPY_GetNamedFunction.restype = ffi.LLVMValueRef  # type: ignore

ffi.lib.LLVMPY_VerifyModule.argtypes = [  # type: ignore
    ffi.LLVMModuleRef,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_VerifyModule.restype = c_bool  # type: ignore

ffi.lib.LLVMPY_GetDataLayout.argtypes = [ffi.LLVMModuleRef, POINTER(c_char_p)]  # type: ignore
ffi.lib.LLVMPY_SetDataLayout.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore

ffi.lib.LLVMPY_GetTarget.argtypes = [ffi.LLVMModuleRef, POINTER(c_char_p)]  # type: ignore
ffi.lib.LLVMPY_SetTarget.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore

ffi.lib.LLVMPY_GetNamedGlobalVariable.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore
ffi.lib.LLVMPY_GetNamedGlobalVariable.restype = ffi.LLVMValueRef  # type: ignore

ffi.lib.LLVMPY_GetNamedStructType.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore
ffi.lib.LLVMPY_GetNamedStructType.restype = ffi.LLVMTypeRef  # type: ignore

ffi.lib.LLVMPY_ModuleGlobalsIter.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_ModuleGlobalsIter.restype = ffi.LLVMGlobalsIterator  # type: ignore

ffi.lib.LLVMPY_DisposeGlobalsIter.argtypes = [ffi.LLVMGlobalsIterator]  # type: ignore

ffi.lib.LLVMPY_GlobalsIterNext.argtypes = [ffi.LLVMGlobalsIterator]  # type: ignore
ffi.lib.LLVMPY_GlobalsIterNext.restype = ffi.LLVMValueRef  # type: ignore

ffi.lib.LLVMPY_ModuleFunctionsIter.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_ModuleFunctionsIter.restype = ffi.LLVMFunctionsIterator  # type: ignore

ffi.lib.LLVMPY_ModuleTypesIter.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_ModuleTypesIter.restype = ffi.LLVMTypesIterator  # type: ignore

ffi.lib.LLVMPY_DisposeFunctionsIter.argtypes = [ffi.LLVMFunctionsIterator]  # type: ignore

ffi.lib.LLVMPY_DisposeTypesIter.argtypes = [ffi.LLVMTypesIterator]  # type: ignore

ffi.lib.LLVMPY_FunctionsIterNext.argtypes = [ffi.LLVMFunctionsIterator]  # type: ignore
ffi.lib.LLVMPY_FunctionsIterNext.restype = ffi.LLVMValueRef  # type: ignore

ffi.lib.LLVMPY_TypesIterNext.argtypes = [ffi.LLVMTypesIterator]  # type: ignore
ffi.lib.LLVMPY_TypesIterNext.restype = ffi.LLVMTypeRef  # type: ignore

ffi.lib.LLVMPY_CloneModule.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_CloneModule.restype = ffi.LLVMModuleRef  # type: ignore

ffi.lib.LLVMPY_GetModuleName.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_GetModuleName.restype = c_char_p  # type: ignore

ffi.lib.LLVMPY_SetModuleName.argtypes = [ffi.LLVMModuleRef, c_char_p]  # type: ignore

ffi.lib.LLVMPY_GetModuleSourceFileName.argtypes = [ffi.LLVMModuleRef]  # type: ignore
ffi.lib.LLVMPY_GetModuleSourceFileName.restype = c_char_p  # type: ignore
