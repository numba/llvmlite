from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# Note: We should probably default to lazy opaque pointers disabled, but I want
# us to be able to test with Numba directly.
def _lazy_opaque_pointers_enabled():
  import os
  return os.environ.get('LLVMLITE_ENABLE_LAZY_OPAQUE_POINTERS', '1') == '1'
lazy_opaque_pointers_enabled = _lazy_opaque_pointers_enabled()
del _lazy_opaque_pointers_enabled
