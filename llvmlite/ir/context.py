from __future__ import annotations

from llvmlite.ir import _utils, types


class Context(object):
    def __init__(self) -> None:
        self.scope = _utils.NameScope()
        self.identified_types: dict[str, types.IdentifiedStructType] = {}

    def get_identified_type(self, name: str) -> types.IdentifiedStructType:
        if name not in self.identified_types:
            self.scope.register(name)
            ty = types.IdentifiedStructType(self, name)
            self.identified_types[name] = ty
        else:
            ty = self.identified_types[name]
        return ty


global_context = Context()
