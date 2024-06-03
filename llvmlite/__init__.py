from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# FIXME: Remove me once typed pointers are no longer supported.
def _get_disable_opaque_pointers():
  import os
  return os.environ.get('LLVMLITE_DISABLE_OPAQUE_POINTERS', '0') == '1'
_disable_opaque_pointers = _get_disable_opaque_pointers()
del _get_disable_opaque_pointers
