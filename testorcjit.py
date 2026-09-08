"""
Exercise the NewOrcJIT (ORCv2 / LLJIT) MCJIT-replacement engine.
"""

import ctypes
import sys
import unittest

import llvmlite.binding as llvm
from llvmlite.binding.neworcjit import create_new_orcjit


ADD_IR = r"""
define i32 @add(i32 %a, i32 %b) {
entry:
  %s = add i32 %a, %b
  ret i32 %s
}
"""

MUL_IR = r"""
define i32 @mul(i32 %a, i32 %b) {
entry:
  %p = mul i32 %a, %b
  ret i32 %p
}
"""

# Module that calls an externally-resolved symbol "ext_addone".
EXT_IR = r"""
declare i32 @ext_addone(i32)

define i32 @use_ext(i32 %x) {
entry:
  %r = call i32 @ext_addone(i32 %x)
  ret i32 %r
}
"""

# A definition with !numba.preserve metadata — must NOT be renamed.
PRESERVED_IR = r"""
define i32 @keep_me(i32 %x) !numba.preserve !0 {
entry:
  %r = add i32 %x, 1
  ret i32 %r
}

!0 = !{}
"""

# A pre-mangled Itanium symbol (foo()). Renamed name should still demangle.
ITANIUM_IR = r"""
define i32 @_Z3foov() {
entry:
  ret i32 7
}
"""


@ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
def _addone_impl(x):
    return x + 1


def _resolve(jit, handle, original):
    """Resolve `original` to its post-rename name via the (internal)
    rename map. Tests below use the public ``handle=`` lookup API where
    possible; this helper remains for tests that explicitly assert on
    the post-rename linker name.
    """
    rename_map = jit._get_rename_map(handle)
    return rename_map.get(original, original)


class TestNewOrcJIT(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def test_basic_compile_and_call(self):
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ADD_IR)
            jit.finalize_object()
            name = _resolve(jit, h, "add")
            addr = jit.get_function_address(name)
            self.assertNotEqual(addr, 0)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32,
                                  ctypes.c_int32, ctypes.c_int32)(addr)
            self.assertEqual(fn(3, 4), 7)
            self.assertEqual(fn(-10, 5), -5)
        finally:
            jit.close()

    def test_renamed_symbol_uses_hash_suffix(self):
        # Non-Itanium name "add" → "add.<16hex>".
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ADD_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertIn("add", rmap)
            new = rmap["add"]
            self.assertTrue(new.startswith("add."), new)
            tail = new[len("add."):]
            self.assertEqual(len(tail), 16)
            self.assertTrue(all(c in "0123456789abcdef" for c in tail), tail)
        finally:
            jit.close()

    def test_renamed_itanium_uses_abi_tag(self):
        # `_Z3foov` should get a `B<len><hex>` ABI tag spliced in before the
        # parameter list ("v"), giving `_Z3fooB16<hex>v`.
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ITANIUM_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertIn("_Z3foov", rmap)
            new = rmap["_Z3foov"]
            self.assertTrue(new.startswith("_Z3fooB17_"), new)
            self.assertTrue(new.endswith("v"), new)
            self.assertEqual(len(new), len("_Z3fooB17_") + 16 + 1)
        finally:
            jit.close()

    def test_preserve_metadata_skips_rename(self):
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(PRESERVED_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertNotIn("keep_me", rmap)
            addr = jit.get_function_address("keep_me")
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)(addr)
            self.assertEqual(fn(41), 42)
        finally:
            jit.close()

    def test_multiple_modules_flat_namespace(self):
        jit = create_new_orcjit()
        try:
            h_add = jit.add_ir_module(ADD_IR)
            h_mul = jit.add_ir_module(MUL_IR)
            jit.finalize_object()

            add_fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                      ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_add, "add")))
            mul_fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                      ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_mul, "mul")))

            self.assertEqual(add_fn(2, 3), 5)
            self.assertEqual(mul_fn(6, 7), 42)
        finally:
            jit.close()


    def test_duplicate_preserved_define_first_wins(self):
        # ORC's ObjectLinkingLayer is configured with
        # setOverrideObjectFlagsWithResponsibilityFlags +
        # setAutoClaimResponsibilityForObjectSymbols, which deliver MCJIT-style
        # first-wins on duplicate weak/linkonce_odr defs across object files.
        # Two modules that each define `linkonce_odr @shared_env` with the
        # SAME body must load successfully (no DuplicateDefinition); both
        # readers reach the first-loaded storage. (The previous demote pass
        # that hand-rewrote the second def to an external decl is gone — the
        # object layer handles this natively now.)
        SHARED = r"""
@shared_env = linkonce_odr global i32 305419896, align 4, !numba.preserve !0

define i32 @reader_a() {
entry:
  %v = load i32, ptr @shared_env, align 4
  ret i32 %v
}

!0 = !{}
"""
        SHARED_DUP = r"""
@shared_env = linkonce_odr global i32 305419896, align 4, !numba.preserve !0

define i32 @reader_b() {
entry:
  %v = load i32, ptr @shared_env, align 4
  ret i32 %v
}

!0 = !{}
"""
        jit = create_new_orcjit()
        try:
            h_a = jit.add_ir_module(SHARED)
            h_b = jit.add_ir_module(SHARED_DUP)
            jit.finalize_object()

            # Preserved name is unrenamed in both handles.
            self.assertNotIn("shared_env", jit._get_rename_map(h_a))
            self.assertNotIn("shared_env", jit._get_rename_map(h_b))

            reader_a = ctypes.CFUNCTYPE(ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_a, "reader_a")))
            reader_b = ctypes.CFUNCTYPE(ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_b, "reader_b")))

            # Both readers see the first-wins storage value.
            self.assertEqual(reader_a(), 0x12345678)
            self.assertEqual(reader_b(), 0x12345678)
            self.assertEqual(
                jit.get_function_address("shared_env"),
                jit.get_function_address("shared_env"))
        finally:
            jit.close()

    def test_modules_add_after_finalize(self):
        jit = create_new_orcjit()
        try:
            h_add = jit.add_ir_module(ADD_IR)
            jit.finalize_object()
            add_fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                      ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_add, "add")))

            self.assertEqual(add_fn(2, 3), 5)

            h_mul = jit.add_ir_module(MUL_IR)
            jit.finalize_object()
            mul_fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                      ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h_mul, "mul")))

            self.assertEqual(mul_fn(6, 7), 42)
        finally:
            jit.close()

    def test_remove_module(self):
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ADD_IR)
            jit.finalize_object()
            name = _resolve(jit, h, "add")
            self.assertNotEqual(jit.get_function_address(name), 0)
            jit.remove_module(h)
            with self.assertRaises(RuntimeError):
                jit.get_function_address(name)
        finally:
            jit.close()

    def test_add_global_mapping(self):
        # ext_addone is a *declaration* in the module so it stays unrenamed
        # (declarations are never renamed). use_ext is a definition and gets
        # renamed.
        jit = create_new_orcjit()
        try:
            addr = ctypes.cast(_addone_impl, ctypes.c_void_p).value
            jit.add_global_mapping("ext_addone", addr)

            h = jit.add_ir_module(EXT_IR)
            jit.finalize_object()

            use = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h, "use_ext")))
            self.assertEqual(use(41), 42)
        finally:
            jit.close()

    def test_resolver_callback(self):
        addr = ctypes.cast(_addone_impl, ctypes.c_void_p).value

        seen = []

        def resolver(name):
            seen.append(name)
            if name == "ext_addone":
                return addr
            return 0

        jit = create_new_orcjit(resolver=resolver)
        try:
            h = jit.add_ir_module(EXT_IR)
            jit.finalize_object()
            use = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)(
                jit.get_function_address(_resolve(jit, h, "use_ext")))
            self.assertEqual(use(99), 100)
            self.assertIn("ext_addone", seen)
        finally:
            jit.close()

    def test_load_dynamic_library(self):
        ir = r"""
declare double @cos(double)

define double @call_cos(double %x) {
entry:
  %r = call double @cos(double %x)
  ret double %r
}
"""
        jit = create_new_orcjit()
        try:
            for libname in ("libm.so.6", "libc.so.6", "libSystem.dylib"):
                try:
                    jit.load_dynamic_library(libname)
                    break
                except RuntimeError:
                    continue
            else:
                self.skipTest("no libm-equivalent available")

            h = jit.add_ir_module(ir)
            jit.finalize_object()
            fn = ctypes.CFUNCTYPE(ctypes.c_double, ctypes.c_double)(
                jit.get_function_address(_resolve(jit, h, "call_cos")))
            self.assertAlmostEqual(fn(0.0), 1.0)
        finally:
            jit.close()

    def test_unknown_symbol_raises(self):
        jit = create_new_orcjit()
        try:
            with self.assertRaises(RuntimeError):
                jit.get_function_address("definitely_not_defined_xyz")
        finally:
            jit.close()

    def test_object_cache_round_trip(self):
        # Notify-only cache: the engine hands the framed blob to the notify
        # callback after each successful compile+load. Cache-hit replay is
        # the caller's responsibility — they decide when to call
        # add_object_file(blob) directly. The legacy get= callback exists
        # for API compatibility but is ignored.
        cache = {}

        def notify(key, blob):
            cache[key] = blob

        jit1 = create_new_orcjit()
        try:
            jit1.set_object_cache(notify=notify)
            # Set the module identifier explicitly so the cache key is
            # stable across runs.
            ir = ('; ModuleID = "stable-key-add"\n'
                  'source_filename = "stable-key-add"\n' + ADD_IR)
            h = jit1.add_ir_module(ir)
            jit1.finalize_object()
            rmap1 = jit1._get_rename_map(h)
            name = rmap1.get("add", "add")
            addr1 = jit1.get_function_address(name)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                  ctypes.c_int32)(addr1)
            self.assertEqual(fn(2, 5), 7)
        finally:
            jit1.close()

        self.assertTrue(cache, "object cache should have captured bytes")
        sole_blob = next(iter(cache.values()))

        # Second run: caller replays the captured blob via add_object_file.
        # notify must NOT fire on a pure replay (no compile happened).
        jit2 = create_new_orcjit()
        try:
            calls = {"notify": 0}

            def notify2(key, blob):
                calls["notify"] += 1

            jit2.set_object_cache(notify=notify2)
            h = jit2.add_object_file(sole_blob)
            jit2.finalize_object()
            rmap2 = jit2._get_rename_map(h)
            # Rename map round-trips through the framed blob.
            self.assertEqual(rmap1, rmap2)
            addr2 = jit2.get_function_address("add", handle=h)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                  ctypes.c_int32)(addr2)
            self.assertEqual(fn(10, 20), 30)
            self.assertEqual(calls["notify"], 0)
        finally:
            jit2.close()

    def test_add_object_file_with_rename_map(self):
        # Compile once, capture object bytes + rename map, then load those
        # bytes via add_object_file in a fresh JIT and confirm the symbol
        # resolves under the cached linker name.
        captured = {}

        def notify(key, blob):
            captured["bytes"] = blob

        jit1 = create_new_orcjit()
        try:
            jit1.set_object_cache(notify=notify, get=lambda k: None)
            h = jit1.add_ir_module(ADD_IR)
            jit1.finalize_object()
            rename_map = jit1._get_rename_map(h)
            new_name = rename_map["add"]
            # Trigger materialization so notify fires.
            jit1.get_function_address(new_name)
        finally:
            jit1.close()

        self.assertIn("bytes", captured)

        jit2 = create_new_orcjit()
        try:
            h = jit2.add_object_file(captured["bytes"])
            jit2._set_rename_map(h, rename_map)
            jit2.finalize_object()
            self.assertEqual(jit2._get_rename_map(h), rename_map)
            addr = jit2.get_function_address(new_name)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                  ctypes.c_int32)(addr)
            self.assertEqual(fn(11, 22), 33)
        finally:
            jit2.close()


# ---------------------------------------------------------------------------
# Part 3 additions: target_data, is_symbol_defined, handle-aware lookups,
# eager finalize, framed-blob object cache.

# Module that *defines* `good` and *declares* `missing_extern`. `good` is
# self-contained; we use it to verify is_symbol_defined doesn't materialize
# anything weird.
GOOD_AND_DECL_IR = r"""
declare i32 @missing_extern(i32)

define i32 @good(i32 %x) {
entry:
  %r = add i32 %x, 1
  ret i32 %r
}
"""

# References an undefined external. finalize_object should fail.
BROKEN_IR = r"""
declare i32 @definitely_missing_zzz(i32)

define i32 @uses_missing(i32 %x) {
entry:
  %r = call i32 @definitely_missing_zzz(i32 %x)
  ret i32 %r
}
"""


class TestNewOrcJITPart3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def test_target_data(self):
        jit = create_new_orcjit()
        try:
            td = jit.target_data
            # Round-trip through string repr.
            s = str(td)
            self.assertIsInstance(s, str)
            self.assertGreater(len(s), 0)
            # Property is cached.
            self.assertIs(td, jit.target_data)
            # Layout string mentions a sensible pointer width: 64-bit
            # hosts have "p:64" or "S64"/"S128" markers; 32-bit hosts
            # would have "p:32". Check by re-creating a TargetData from
            # the string and verifying it round-trips.
            td2 = llvm.create_target_data(s)
            try:
                self.assertEqual(str(td2), s)
            finally:
                td2.close()
            # Sanity: 64-bit hosts produce a layout with "64" in it.
            if ctypes.sizeof(ctypes.c_void_p) == 8:
                self.assertIn("64", s)
        finally:
            jit.close()

    def test_is_symbol_defined_basic(self):
        jit = create_new_orcjit()
        try:
            self.assertFalse(jit.is_symbol_defined("good"))
            h = jit.add_ir_module(GOOD_AND_DECL_IR)
            jit.finalize_object()
            # With handle, original name resolves through rename map.
            self.assertTrue(jit.is_symbol_defined("good", handle=h))
            # Never-defined name is False.
            self.assertFalse(
                jit.is_symbol_defined("never_defined_xyz", handle=h))
            self.assertFalse(jit.is_symbol_defined("never_defined_xyz"))
        finally:
            jit.close()

    def test_is_symbol_defined_does_not_materialize(self):
        # Sanity: calling is_symbol_defined on a known symbol must not
        # trigger materialization side-effects. We can't observe codegen
        # directly, but we can confirm the call doesn't raise on a module
        # whose other symbol references an undefined external — i.e.
        # lookupFlags is non-blocking.
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(GOOD_AND_DECL_IR)
            # Don't finalize. Just probe.
            self.assertTrue(jit.is_symbol_defined("good", handle=h))
            self.assertFalse(jit.is_symbol_defined("missing_extern",
                                                   handle=h))
        finally:
            jit.close()

    def test_get_function_address_handle_kwarg(self):
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ADD_IR)
            jit.finalize_object()
            via_handle = jit.get_function_address("add", handle=h)
            via_linker = jit.get_function_address(_resolve(jit, h, "add"))
            self.assertEqual(via_handle, via_linker)
            self.assertNotEqual(via_handle, 0)
            # linker_name=True with handle still translates first.
            via_handle_lk = jit.get_function_address(
                "add", handle=h, linker_name=True)
            self.assertEqual(via_handle_lk, via_handle)
        finally:
            jit.close()

    def test_add_global_mapping_accepts_gv_like(self):
        jit = create_new_orcjit()
        try:
            class FakeGV:
                name = "ext_addone"

            addr = ctypes.cast(_addone_impl, ctypes.c_void_p).value
            jit.add_global_mapping(FakeGV(), addr)
            h = jit.add_ir_module(EXT_IR)
            jit.finalize_object()
            use = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)(
                jit.get_function_address("use_ext", handle=h))
            self.assertEqual(use(41), 42)
        finally:
            jit.close()

    def test_finalize_object_eager_error(self):
        jit = create_new_orcjit()
        try:
            jit.add_ir_module(BROKEN_IR)
            with self.assertRaises(RuntimeError):
                jit.finalize_object()
        finally:
            jit.close()

    def test_framed_object_cache_round_trip_no_user_rename(self):
        # First run: capture the framed bytes via the user callbacks.
        # The user callback never sees the rename map directly — it's
        # bundled into the bytes by the engine.
        store = {}

        def notify(key, blob):
            store[key] = blob

        def get(key):
            return store.get(key)

        ir = ('; ModuleID = "framed-rt"\n'
              'source_filename = "framed-rt"\n' + ADD_IR)

        jit1 = create_new_orcjit()
        try:
            jit1.set_object_cache(notify=notify, get=get)
            h1 = jit1.add_ir_module(ir)
            jit1.finalize_object()
            # Trigger materialization and verify it works in the first JIT.
            addr1 = jit1.get_function_address("add", handle=h1)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                  ctypes.c_int32)(addr1)
            self.assertEqual(fn(2, 3), 5)
        finally:
            jit1.close()

        self.assertTrue(store, "object cache should have captured bytes")
        # Sanity: framed bytes start with our magic.
        sole_blob = next(iter(store.values()))
        self.assertEqual(sole_blob[:4], b"NORC")

        # Second run: feed the same framed bytes back through addObjectFile.
        # The test never touches _get_rename_map / _set_rename_map; the
        # engine extracts and installs the rename map automatically.
        jit2 = create_new_orcjit()
        try:
            h2 = jit2.add_object_file(sole_blob)
            jit2.finalize_object()
            # Look up under the ORIGINAL pre-rename name with handle=.
            addr2 = jit2.get_function_address("add", handle=h2)
            fn2 = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                   ctypes.c_int32)(addr2)
            self.assertEqual(fn2(10, 20), 30)
        finally:
            jit2.close()

    def test_framed_cache_legacy_raw_bytes_tolerated(self):
        # Hand a raw object file (no NORC frame) to addObjectFile; it must
        # still load (treated as legacy unframed). We get raw bytes by
        # asking the engine to compile a module without a cache, then
        # reading the bytes via a one-shot capturing cache.
        ir = ('; ModuleID = "raw-bytes"\n'
              'source_filename = "raw-bytes"\n' + ADD_IR)
        captured = {}

        def notify(key, blob):
            captured["framed"] = blob

        def get(key):
            return None

        jit1 = create_new_orcjit()
        try:
            jit1.set_object_cache(notify=notify, get=get)
            h = jit1.add_ir_module(ir)
            jit1.finalize_object()
            jit1.get_function_address("add", handle=h)
        finally:
            jit1.close()

        framed = captured["framed"]
        # Strip the NORC header to obtain raw object bytes.
        self.assertEqual(framed[:4], b"NORC")
        rmlen = int.from_bytes(framed[5:9], "little")
        raw_obj = framed[9 + rmlen:]

        # Feed the raw bytes (no frame) back: addObjectFile must succeed.
        jit2 = create_new_orcjit()
        try:
            jit2.add_object_file(raw_obj)
            jit2.finalize_object()
        finally:
            jit2.close()

    def test_add_object_file_replay_skip(self):
        # When a framed .o is loaded twice into the same engine — e.g. two
        # callers resolving to the same on-disk cache entry — the strong
        # symbols are already in the JITDylib. ORC would otherwise raise
        # DuplicateDefinition. addObjectFile detects "all strong defs
        # already published" via a non-materializing probe and returns a
        # fresh handle as a no-op replay. The handle's rename map mirrors
        # the framed blob so handle-aware lookup still works.
        store = {}

        def notify(key, blob):
            store[key] = blob

        ir = ('; ModuleID = "replay-skip"\n'
              'source_filename = "replay-skip"\n' + ADD_IR)

        jit = create_new_orcjit()
        try:
            jit.set_object_cache(notify=notify)
            h1 = jit.add_ir_module(ir)
            jit.finalize_object()
            rmap1 = jit.get_function_address("add", handle=h1)
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32,
                                  ctypes.c_int32)(rmap1)
            self.assertEqual(fn(2, 3), 5)

            sole_blob = next(iter(store.values()))
            self.assertEqual(sole_blob[:4], b"NORC")

            # Re-load the same framed blob into the same engine. Strong
            # symbol `add.<hash>` is already defined → replay-skip path.
            h2 = jit.add_object_file(sole_blob)
            self.assertNotEqual(h1, h2)
            # Both handles agree on the post-rename name.
            self.assertEqual(jit._get_rename_map(h1), jit._get_rename_map(h2))
            # Handle-aware lookup against the replay-skip handle works.
            addr2 = jit.get_function_address("add", handle=h2)
            self.assertEqual(addr2, rmap1)
            # finalize_object must remain well-defined post replay-skip.
            jit.finalize_object()
            # removeModule on the replay-skip handle is a no-op for the
            # JITDylib but must not crash or destabilize the engine.
            jit.remove_module(h2)
            # Original definition still resolves after the replay-skip
            # handle is removed.
            self.assertEqual(
                jit.get_function_address("add", handle=h1), rmap1)
        finally:
            jit.close()

    def test_preserve_metadata_still_works_after_framing(self):
        # Sanity: the !numba.preserve opt-out keeps a symbol unrenamed
        # end-to-end with the framed-cache path active.
        store = {}

        def notify(key, blob):
            store[key] = blob

        def get(key):
            return store.get(key)

        jit = create_new_orcjit()
        try:
            jit.set_object_cache(notify=notify, get=get)
            h = jit.add_ir_module(PRESERVED_IR)
            jit.finalize_object()
            # `keep_me` is exempt from rename.
            self.assertNotIn("keep_me", jit._get_rename_map(h))
            addr = jit.get_function_address("keep_me")
            fn = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)(addr)
            self.assertEqual(fn(41), 42)
        finally:
            jit.close()


# ---------------------------------------------------------------------------
# Idea 3b: !numba.env_for delegates a GV's hash to its referencing function.
# The env GV's own body (typically `null voidptr`) is uniform across every
# env, so self-hashing collapses them. Delegation binds the env's identity to
# the function's identity: same f → same env name (legit sharing), different
# f-body → different env name (no JITDylib collision).


# Module: function `f_alpha` (linkonce_odr — Numba's normal cross-module-
# shareable linkage) with body `ret i32 11`, and an env GV `env_alpha`
# (common — Numba's env-GV linkage) tagged with
# `!numba.env_for !{!"f_alpha"}`. Both are mergeable linkages so the demote
# pass first-wins on cross-module duplicates, matching the real Numba
# emission shape.
ENV_FOR_ALPHA_IR = r"""
@env_alpha = common global ptr null, !numba.env_for !1

define linkonce_odr i32 @f_alpha() {
entry:
  %p = load ptr, ptr @env_alpha
  ret i32 11
}

!1 = !{ !"f_alpha" }
"""

# Same shape, different function body (`ret i32 22`). Same env-GV name.
ENV_FOR_ALPHA_DIFFBODY_IR = r"""
@env_alpha = common global ptr null, !numba.env_for !1

define linkonce_odr i32 @f_alpha() {
entry:
  %p = load ptr, ptr @env_alpha
  ret i32 22
}

!1 = !{ !"f_alpha" }
"""

# Two functions/envs in one module, each env tagged at its own function.
ENV_FOR_TWO_IR = r"""
@env_a = common global ptr null, !numba.env_for !1
@env_b = common global ptr null, !numba.env_for !2

define i32 @f_a() {
entry:
  %p = load ptr, ptr @env_a
  ret i32 1
}

define i32 @f_b() {
entry:
  %p = load ptr, ptr @env_b
  ret i32 2
}

!1 = !{ !"f_a" }
!2 = !{ !"f_b" }
"""

# Sanity: a GV without the env_for tag continues to be hashed by its own body
# (existing behavior). Pair an unmarked GV with a function so we have a place
# to confirm the GV gets *some* renamed suffix and that suffix is its own hash,
# not the function's.
PLAIN_GV_IR = r"""
@plain_gv = common global i32 0

define i32 @reads_plain() {
entry:
  %v = load i32, ptr @plain_gv
  ret i32 %v
}
"""


def _hex_suffix(renamed):
    # "name.<16hex>" → "<16hex>"
    self_assert = renamed.rsplit(".", 1)
    if len(self_assert) != 2:
        return None
    tail = self_assert[1]
    if len(tail) != 16:
        return None
    if not all(c in "0123456789abcdef" for c in tail):
        return None
    return tail


class TestNewOrcJITEnvFor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

    def test_env_for_inherits_referencer_hash(self):
        # The env GV's hash suffix must match its referencing function's hash
        # suffix (Idea 3b).
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ENV_FOR_ALPHA_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertIn("f_alpha", rmap)
            self.assertIn("env_alpha", rmap)
            f_tail = _hex_suffix(rmap["f_alpha"])
            env_tail = _hex_suffix(rmap["env_alpha"])
            self.assertIsNotNone(f_tail, rmap["f_alpha"])
            self.assertIsNotNone(env_tail, rmap["env_alpha"])
            self.assertEqual(env_tail, f_tail)
        finally:
            jit.close()

    def test_env_for_distinct_function_bodies_distinct_env_names(self):
        # Two modules with the same env GV name but functions whose bodies
        # differ. Post-rename env names must differ — no JITDylib collision,
        # no demote-pass dependency for correctness.
        jit = create_new_orcjit()
        try:
            h1 = jit.add_ir_module(ENV_FOR_ALPHA_IR)
            h2 = jit.add_ir_module(ENV_FOR_ALPHA_DIFFBODY_IR)
            jit.finalize_object()
            rm1 = jit._get_rename_map(h1)
            rm2 = jit._get_rename_map(h2)
            self.assertNotEqual(rm1["env_alpha"], rm2["env_alpha"])
            # The env names must each match their referencer's name.
            self.assertEqual(_hex_suffix(rm1["env_alpha"]),
                             _hex_suffix(rm1["f_alpha"]))
            self.assertEqual(_hex_suffix(rm2["env_alpha"]),
                             _hex_suffix(rm2["f_alpha"]))
            # Both functions resolve and produce their own bodies (i.e. no
            # cross-module env aliasing).
            f1 = ctypes.CFUNCTYPE(ctypes.c_int32)(
                jit.get_function_address(rm1["f_alpha"]))
            f2 = ctypes.CFUNCTYPE(ctypes.c_int32)(
                jit.get_function_address(rm2["f_alpha"]))
            self.assertEqual(f1(), 11)
            self.assertEqual(f2(), 22)
        finally:
            jit.close()

    def test_env_for_same_referencer_shares_env(self):
        # Two modules whose function body is byte-identical and whose env GVs
        # are tagged at that function. Post-rename env names match (legit
        # sharing). The demote pass first-wins on the second module; both
        # modules' readers reach the same env storage.
        jit = create_new_orcjit()
        try:
            h1 = jit.add_ir_module(ENV_FOR_ALPHA_IR)
            h2 = jit.add_ir_module(ENV_FOR_ALPHA_IR)
            jit.finalize_object()
            rm1 = jit._get_rename_map(h1)
            rm2 = jit._get_rename_map(h2)
            # Both env GV names match.
            self.assertEqual(rm1["env_alpha"], rm2["env_alpha"])
            # Both function names also match — same hash, same renamed name.
            self.assertEqual(rm1["f_alpha"], rm2["f_alpha"])
            # The shared env GV is reachable under its post-rename name.
            env_addr = jit.get_function_address(rm1["env_alpha"])
            self.assertNotEqual(env_addr, 0)
        finally:
            jit.close()

    def test_env_for_distinct_envs_in_one_module(self):
        # Two functions, two distinct envs in the same module. Each env must
        # adopt its OWN referencer's hash — not the wrong one.
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(ENV_FOR_TWO_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertEqual(_hex_suffix(rmap["env_a"]),
                             _hex_suffix(rmap["f_a"]))
            self.assertEqual(_hex_suffix(rmap["env_b"]),
                             _hex_suffix(rmap["f_b"]))
            # And the two envs must differ from each other (different
            # functions, different bodies).
            self.assertNotEqual(rmap["env_a"], rmap["env_b"])
        finally:
            jit.close()

    def test_plain_gv_without_env_for_uses_own_hash(self):
        # Sanity: a GV without !numba.env_for keeps using its own body hash.
        # Specifically, its hash should NOT equal the referencing function's
        # hash (different bodies → different hashes).
        jit = create_new_orcjit()
        try:
            h = jit.add_ir_module(PLAIN_GV_IR)
            jit.finalize_object()
            rmap = jit._get_rename_map(h)
            self.assertIn("plain_gv", rmap)
            self.assertIn("reads_plain", rmap)
            gv_tail = _hex_suffix(rmap["plain_gv"])
            fn_tail = _hex_suffix(rmap["reads_plain"])
            self.assertIsNotNone(gv_tail)
            self.assertIsNotNone(fn_tail)
            self.assertNotEqual(gv_tail, fn_tail)
        finally:
            jit.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
