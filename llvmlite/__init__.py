from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

# FIXME: Remove me once typed pointers are no longer supported.
# Opaque pointers unconditionally required for later LLVM versions
opaque_pointers_enabled = True
# We default to IR layer typed pointers being enabled, since they're needed in
# the most common usage scenarios with later LLVMs.
def _ir_layer_typed_pointers_enabled():
  import os
  return os.environ.get('LLVMLITE_ENABLE_IR_LAYER_TYPED_POINTERS', '1') == '1'
ir_layer_typed_pointers_enabled = _ir_layer_typed_pointers_enabled()
del _ir_layer_typed_pointers_enabled
