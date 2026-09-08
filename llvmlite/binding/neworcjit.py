"""
Python binding for the ORCv2 / LLJIT MCJIT-replacement engine in
``ffi/neworcjit.cpp``.

Design notes:

* Content-hash symbol renaming. Each definition's IR is SHA-256 hashed
  and the hash is spliced into the linker name (Itanium ABI tag aware).
  Symbols with ``!numba.preserve`` metadata on the GlobalValue are exempt
  (NRT helpers, externs registered via ``ll.add_symbol``).
  Symbols with ``!numba.env_for !{!"<funcname>"}`` adopt the named
  function's hash (Numba env GVs whose body is uniform).
  Pre/post rename map is exposed via ``_get_rename_map`` (internal —
  ordinary callers go through the handle-aware lookup APIs).

* Unified emit-then-load pipeline. ``add_ir_module`` and
  ``compile_and_add`` route through ``parseAndCompileAndAdd`` in C++,
  which renames, emits a ``.o`` via the engine's TargetMachine, frames
  it (``NORC || rename_map || object_bytes``), and loads via the
  ORC object layer. The IRCompileLayer is not used; this avoids ORC's
  ``IRMaterializationUnit`` duplicate-symbol assertion and lets the
  ObjectLinkingLayer's first-wins flags handle weak/linkonce_odr
  collisions across .o's transparently. ``add_object_file`` is the
  cache-hit fast path; it parses the framed prefix and installs the
  rename map on the returned handle automatically.

* On-disk object caching. Install a notify callback via
  ``set_object_cache``; the engine fires it once per successful
  compile+load with the framed blob. There is no get callback —
  cache hits are replayed by handing the blob to ``add_object_file``
  directly. Numba's ``CPUCodeLibrary._on_object_compiled`` is the
  expected client of the notify callback; its ``_unserialize`` path
  hands the cached blob back to ``add_object_file`` on cache hit.
"""

import ctypes
from ctypes import (
    CFUNCTYPE, POINTER, c_char, c_char_p, c_int, c_size_t, c_uint64,
)

from llvmlite.binding import ffi, targets
from llvmlite.binding.common import _encode_string


_NewOrcJITRef = ctypes.c_void_p

# Resolver: given an unmangled symbol name, return its address as a uint64,
# or 0 if "I don't know it".
_NumbaResolverCallback = CFUNCTYPE(c_uint64, c_char_p)

# Object cache notify callback. compileAndAdd invokes it once per successful
# emit-and-load with the framed blob. The engine hands the *module
# identifier* string as the cache key — the caller is expected to set
# Module::ModuleIdentifier to a stable hash before adding the module.
_ObjCacheNotifyFn = CFUNCTYPE(None, c_char_p, POINTER(c_char), c_size_t)


class NewOrcJIT(ffi.ObjectRef):
    """An ORCv2-based JIT engine with MCJIT-shaped semantics."""

    def __init__(self, ptr, resolver_cb):
        self._resolver_cb = resolver_cb
        # Object cache bookkeeping — keep the trampoline alive while installed.
        self._cache_notify_cb = None
        super().__init__(ptr)

    def add_ir_module(self, llvmir, module_id=None):
        """Parse *llvmir* and add it as a module. Returns an opaque handle.

        *module_id* sets the parsed Module's identifier — which the engine's
        ObjectCache callbacks see as the cache key. Defaults to the
        ``.name`` attribute of *llvmir* (an llvmlite ``Module``); pass an
        explicit string when feeding raw IR text or to override.
        """
        ir = _encode_string(str(llvmir))
        if module_id is None:
            module_id = getattr(llvmir, "name", None) or ""
        mod_id = _encode_string(module_id)
        with ffi.OutputString() as outerr:
            handle = ffi.lib.LLVMPY_NewOrcJIT_AddIRModule(
                self, ir, mod_id, outerr)
            if not handle:
                raise RuntimeError(str(outerr))
        return int(handle)

    def compile_and_add(self, llvmir, module_id=None):
        """Unified emit-then-load entrypoint.

        Renames *llvmir* by content hash, emits a `.o` via the engine's
        TargetMachine, frames it (NORC || RM || object bytes), loads via
        the object layer, and returns ``(handle, framed_blob_bytes)``.

        The framed blob is suitable for direct on-disk caching — no
        ObjectCache notify/get round-trip is required. ``add_object_file``
        of the same blob on a future engine reproduces the same handle
        shape.
        """
        ir = _encode_string(str(llvmir))
        if module_id is None:
            module_id = getattr(llvmir, "name", None) or ""
        mod_id = _encode_string(module_id)
        out_blob = POINTER(c_char)()
        out_len = c_size_t(0)
        with ffi.OutputString() as outerr:
            handle = ffi.lib.LLVMPY_NewOrcJIT_CompileAndAdd(
                self, ir, mod_id,
                ctypes.byref(out_blob), ctypes.byref(out_len), outerr)
            if not handle:
                raise RuntimeError(str(outerr))
        try:
            blob = ctypes.string_at(out_blob, out_len.value)
        finally:
            ffi.lib.LLVMPY_DisposeString(out_blob)
        return int(handle), blob

    def add_object_file(self, data, name="<jit-obj>"):
        """
        Add a precompiled object file (cache-hit fast path). *data* is bytes.
        Returns a handle equivalent to the one :meth:`add_ir_module` returns.
        """
        buf = bytes(data)
        arr = (c_char * len(buf)).from_buffer_copy(buf)
        with ffi.OutputString() as outerr:
            handle = ffi.lib.LLVMPY_NewOrcJIT_AddObjectFile(
                self, arr, c_size_t(len(buf)),
                _encode_string(name), outerr)
            if not handle:
                raise RuntimeError(str(outerr))
        return int(handle)

    def remove_module(self, handle):
        """Remove a previously added module by handle."""
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_NewOrcJIT_RemoveModule(
                    self, c_uint64(handle), outerr):
                raise RuntimeError(str(outerr))

    def add_global_mapping(self, name_or_gv, address):
        """
        Install an absolute definition at the given address.

        *name_or_gv* may be a string symbol name, or any object with a
        ``.name`` attribute (e.g. an ``llvmlite.ir.GlobalValue``).
        """
        if isinstance(name_or_gv, str):
            name = name_or_gv
        else:
            name = getattr(name_or_gv, "name", None)
            if not isinstance(name, str):
                raise TypeError(
                    "add_global_mapping: expected str or object with "
                    "a .name attribute, got %r" % (name_or_gv,))
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_NewOrcJIT_AddGlobalMapping(
                    self, _encode_string(name), c_uint64(address), outerr):
                raise RuntimeError(str(outerr))

    def _translate_name(self, name, handle):
        """Apply the per-handle rename map if a handle is given."""
        if handle is None:
            return name
        rmap = self._get_rename_map(handle)
        return rmap.get(name, name)

    def get_function_address(self, name, *, handle=None, linker_name=False):
        """
        Look up *name* and return its address as an integer.

        When *handle* is given, *name* is the original (pre-rename) symbol
        name; the engine consults the handle's rename map automatically.
        Pass ``handle=None`` to look up *name* directly as a linker name
        (cross-library use case). Pass ``linker_name=True`` to also bypass
        platform mangling.
        """
        translated = self._translate_name(name, handle)
        with ffi.OutputString() as outerr:
            addr = ffi.lib.LLVMPY_NewOrcJIT_GetFunctionAddress(
                self, _encode_string(translated),
                c_int(1 if linker_name else 0), outerr)
            if not addr:
                msg = str(outerr)
                if msg:
                    raise RuntimeError(msg)
        return int(addr)

    def is_symbol_defined(self, name, *, handle=None):
        """
        Non-materializing existence check. Returns True if *name* is a
        defined symbol in the engine's main JITDylib.

        When *handle* is given, *name* is the original (pre-rename) symbol
        name; the engine consults the handle's rename map automatically.
        """
        translated = self._translate_name(name, handle)
        return bool(ffi.lib.LLVMPY_NewOrcJIT_IsSymbolDefined(
            self, _encode_string(translated)))

    @property
    def target_data(self):
        """The :class:`TargetData` for this engine's TargetMachine.

        Shape-compatible with :attr:`ExecutionEngine.target_data`.
        """
        td = getattr(self, "_td", None)
        if td is not None:
            return td
        ptr = ffi.lib.LLVMPY_NewOrcJIT_GetDataLayoutString(self)
        layout = ffi.ret_string(ptr)
        self._td = targets.create_target_data(layout)
        return self._td

    def load_dynamic_library(self, path):
        """dlopen *path* and expose its symbols to JIT'd code."""
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_NewOrcJIT_LoadDynamicLibrary(
                    self, _encode_string(path), outerr):
                raise RuntimeError(str(outerr))

    def finalize_object(self):
        """Run static initializers for the JITDylib."""
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_NewOrcJIT_Finalize(self, outerr):
                raise RuntimeError(str(outerr))

    def run_static_destructors(self):
        """Run static destructors for the JITDylib."""
        with ffi.OutputString() as outerr:
            if ffi.lib.LLVMPY_NewOrcJIT_RunStaticDestructors(self, outerr):
                raise RuntimeError(str(outerr))

    def _get_rename_map(self, handle):
        """
        Internal: return the ``{original_name: linker_name}`` map for
        symbols the renamer rewrote in the module identified by *handle*.

        Not part of the public API — callers should use
        ``get_function_address(name, handle=...)`` and
        ``is_symbol_defined(name, handle=...)``, both of which consult the
        rename map automatically.
        """
        out_len = c_size_t(0)
        out_ptr = c_char_p(None)
        ffi.lib.LLVMPY_NewOrcJIT_GetRenameMap(
            self, c_uint64(handle), ctypes.byref(out_ptr), ctypes.byref(out_len)
        )
        if not out_ptr or out_len.value == 0:
            return {}
        try:
            buf = ctypes.string_at(out_ptr, out_len.value)
            # Decode alternating null-terminated old/new pairs.
            parts = buf.split(b"\x00")
            # split yields trailing empty string after final null; drop it.
            if parts and parts[-1] == b"":
                parts = parts[:-1]
            out = {}
            for i in range(0, len(parts) - 1, 2):
                out[parts[i].decode("utf-8")] = parts[i + 1].decode("utf-8")
            return out
        finally:
            ffi.lib.LLVMPY_DisposeString(out_ptr)

    def _set_rename_map(self, handle, mapping):
        """
        Internal: restore a rename map for *handle*. Kept as an internal
        entry point because the framed-blob ObjectCache machinery installs
        rename maps automatically; ordinary callers should never need this.
        """
        chunks = []
        for old, new in mapping.items():
            chunks.append(old.encode("utf-8"))
            chunks.append(b"\x00")
            chunks.append(new.encode("utf-8"))
            chunks.append(b"\x00")
        buf = b"".join(chunks)
        ffi.lib.LLVMPY_NewOrcJIT_SetRenameMap(
            self, c_uint64(handle), buf, c_size_t(len(buf)))

    def set_object_cache(self, notify=None, get=None):
        """
        Install the framed-blob notify callback.

        *notify(key: str, blob: bytes)* — fires once per successful
        ``compile_and_add`` (i.e. each IR module submitted via
        :meth:`add_ir_module` / :meth:`compile_and_add`) with the
        framed-blob bytes (``NORC`` header + rename map + object bytes).
        The caller typically writes them to disk, keyed by the module
        identifier string (which is passed as ``key``).

        The legacy *get* parameter is accepted for source compatibility
        but ignored — cache hits are replayed through
        :meth:`add_object_file` directly, not via an ORC-side fetch
        callback. Pass ``notify=None`` to uninstall.
        """
        del get  # unused; kept for source compatibility
        if notify is None:
            self._cache_notify_cb = None
            ffi.lib.LLVMPY_NewOrcJIT_SetObjectCache(self, _ObjCacheNotifyFn(0))
            return

        def _notify_trampoline(key, bytes_ptr, length):
            try:
                key_str = key.decode("utf-8") if key else ""
                blob = ctypes.string_at(bytes_ptr, length)
                notify(key_str, blob)
            except Exception:
                pass

        self._cache_notify_cb = _ObjCacheNotifyFn(_notify_trampoline)
        ffi.lib.LLVMPY_NewOrcJIT_SetObjectCache(self, self._cache_notify_cb)

    def _dispose(self):
        self._capi.LLVMPY_NewOrcJIT_Dispose(self)


def create_new_orcjit(resolver=None, *, use_process_symbols=True) -> NewOrcJIT:
    """Create a :class:`NewOrcJIT` for the host machine.

    When *use_process_symbols* is true (the default), the engine attaches a
    process-symbol generator to its main JITDylib so that both
    ``ll.add_symbol`` entries and ``dlsym`` of the host process resolve from
    JIT'd code — matching MCJIT's behaviour.
    """
    if resolver is None:
        cb = _NumbaResolverCallback(lambda name: 0)
    else:
        def _trampoline(name):
            try:
                return int(resolver(name.decode("utf-8")) or 0)
            except Exception:
                return 0
        cb = _NumbaResolverCallback(_trampoline)

    with ffi.OutputString() as outerr:
        ptr = ffi.lib.LLVMPY_NewOrcJIT_Create(
            cb, c_int(1 if use_process_symbols else 0), outerr)
        if not ptr:
            raise RuntimeError(str(outerr))
    return NewOrcJIT(ptr, cb)


# =============================================================================
# C function prototypes

ffi.lib.LLVMPY_NewOrcJIT_Create.argtypes = [
    _NumbaResolverCallback, c_int, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_Create.restype = _NewOrcJITRef

ffi.lib.LLVMPY_NewOrcJIT_Dispose.argtypes = [_NewOrcJITRef]

ffi.lib.LLVMPY_NewOrcJIT_AddIRModule.argtypes = [
    _NewOrcJITRef, c_char_p, c_char_p, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_AddIRModule.restype = c_uint64

ffi.lib.LLVMPY_NewOrcJIT_CompileAndAdd.argtypes = [
    _NewOrcJITRef, c_char_p, c_char_p,
    POINTER(POINTER(c_char)), POINTER(c_size_t), POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_CompileAndAdd.restype = c_uint64

ffi.lib.LLVMPY_NewOrcJIT_AddObjectFile.argtypes = [
    _NewOrcJITRef, POINTER(c_char), c_size_t, c_char_p, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_AddObjectFile.restype = c_uint64

ffi.lib.LLVMPY_NewOrcJIT_RemoveModule.argtypes = [
    _NewOrcJITRef, c_uint64, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_RemoveModule.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_AddGlobalMapping.argtypes = [
    _NewOrcJITRef, c_char_p, c_uint64, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_AddGlobalMapping.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_GetFunctionAddress.argtypes = [
    _NewOrcJITRef, c_char_p, c_int, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_GetFunctionAddress.restype = c_uint64

ffi.lib.LLVMPY_NewOrcJIT_LoadDynamicLibrary.argtypes = [
    _NewOrcJITRef, c_char_p, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_LoadDynamicLibrary.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_Finalize.argtypes = [_NewOrcJITRef, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_Finalize.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_RunStaticDestructors.argtypes = [
    _NewOrcJITRef, POINTER(c_char_p)]
ffi.lib.LLVMPY_NewOrcJIT_RunStaticDestructors.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_GetRenameMap.argtypes = [
    _NewOrcJITRef, c_uint64, POINTER(c_char_p), POINTER(c_size_t)]
ffi.lib.LLVMPY_NewOrcJIT_GetRenameMap.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_SetRenameMap.argtypes = [
    _NewOrcJITRef, c_uint64, c_char_p, c_size_t]

ffi.lib.LLVMPY_NewOrcJIT_SetObjectCache.argtypes = [
    _NewOrcJITRef, _ObjCacheNotifyFn]

ffi.lib.LLVMPY_NewOrcJIT_IsSymbolDefined.argtypes = [_NewOrcJITRef, c_char_p]
ffi.lib.LLVMPY_NewOrcJIT_IsSymbolDefined.restype = c_int

ffi.lib.LLVMPY_NewOrcJIT_GetDataLayoutString.argtypes = [_NewOrcJITRef]
ffi.lib.LLVMPY_NewOrcJIT_GetDataLayoutString.restype = ctypes.c_void_p
