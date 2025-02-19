from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# FIXME: Remove me once typed pointers are no longer supported.
# Let's enable opaque pointers unconditionally.
opaque_pointers_enabled = True
# We default to lazy opaque pointers being enabled, since they're needed in the
# most common usage scenarios with  later LLVMs
def _lazy_opaque_pointers_enabled():
  import os
  return os.environ.get('LLVMLITE_ENABLE_LAZY_OPAQUE_POINTERS', '1') == '1'
lazy_opaque_pointers_enabled = _lazy_opaque_pointers_enabled()
del _lazy_opaque_pointers_enabled
