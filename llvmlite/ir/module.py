from __future__ import annotations

import collections
from typing import Any, Iterable, NoReturn, OrderedDict, Sequence

from llvmlite.ir import _utils, context, types, values


class Module:
    def __init__(
        self,
        name: str = "",
        # this one is fine with pylance, but not with mypy for some reason
        context: context.Context = context.global_context,  # type: ignore
    ) -> None:
        self.context = context
        self.name = name  # name is for debugging/informational
        self.data_layout = ""
        self.scope = _utils.NameScope()
        self.triple = "unknown-unknown-unknown"
        self.globals: OrderedDict[
            str, values.GlobalVariable
        ] = collections.OrderedDict()
        # Innamed metadata nodes.
        self.metadata: list[values.MDValue | values.DIValue] = []
        # Named metadata nodes
        self.namedmetadata: dict[str, values.NamedMetaData] = {}
        # Cache for metadata node deduplication
        self._metadatacache: dict[Any, Any] = {}

    def _fix_metadata_operands(
        self, operands: list[Iterable[values.Value] | str | None]
    ) -> list[types.MetaDataType | values.MetaDataString | values.MDValue]:
        op: Any
        fixed_ops: list[Any] = []
        for op in operands:
            if op is None:
                # A literal None creates a null metadata value
                op = types.MetaDataType()(None)
            elif isinstance(op, str):
                # A literal string creates a metadata string value
                op = values.MetaDataString(self, op)
            elif isinstance(op, (list, tuple)):
                # A sequence creates a metadata node reference
                op = self.add_metadata(op)  # type: ignore
            fixed_ops.append(op)
        return fixed_ops

    def _fix_di_operands(
        self, operands: Iterable[tuple[str, values.Value]]
    ) -> list[tuple[str, values.MDValue]]:
        fixed_ops = []
        for name, op in operands:
            if isinstance(op, (list, tuple)):
                # A sequence creates a metadata node reference
                op = self.add_metadata(op)  # type: ignore
            fixed_ops.append((name, op))  # type: ignore
        return fixed_ops  # type: ignore

    def add_metadata(
        self,
        operands: list[values.Constant],
    ) -> values.MDValue:
        """
        Add an unnamed metadata to the module with the given *operands*
        (a sequence of values) or return a previous equivalent metadata.
        A MDValue instance is returned, it can then be associated to
        e.g. an instruction.
        """
        if not isinstance(operands, (list, tuple)):
            raise TypeError(
                "expected a list or tuple of metadata values, "
                "got {0!r}".format(operands)
            )
        operands = self._fix_metadata_operands(operands)  # type: ignore
        key = tuple(operands)
        if key not in self._metadatacache:
            n = len(self.metadata)
            md = values.MDValue(self, operands, name=str(n))
            self._metadatacache[key] = md
        else:
            md = self._metadatacache[key]
        return md

    def add_debug_info(
        self, kind: str, operands: dict[str, values.Value], is_distinct: bool = False
    ) -> values.DIValue:
        """
        Add debug information metadata to the module with the given
        *operands* (a dict of values with string keys) or return
        a previous equivalent metadata.  *kind* is a string of the
        debug information kind (e.g. "DICompileUnit").

        A DIValue instance is returned, it can then be associated to e.g.
        an instruction.
        """
        op_tuple = tuple(sorted(self._fix_di_operands(operands.items())))
        key = (kind, op_tuple, is_distinct)
        if key not in self._metadatacache:
            n = len(self.metadata)
            di = values.DIValue(self, is_distinct, kind, op_tuple, name=str(n))
            self._metadatacache[key] = di
        else:
            di = self._metadatacache[key]
        return di

    def add_named_metadata(
        self, name: str, element: None = None
    ) -> values.NamedMetaData:
        """
        Add a named metadata node to the module, if it doesn't exist,
        or return the existing node.
        If *element* is given, it will append a new element to
        the named metadata node.  If *element* is a sequence of values
        (rather than a metadata value), a new unnamed node will first be
        created.

        Example::
            module.add_named_metadata("llvm.ident", ["llvmlite/1.0"])
        """
        if name in self.namedmetadata:
            nmd = self.namedmetadata[name]
        else:
            nmd = self.namedmetadata[name] = values.NamedMetaData(self)  # type: ignore
        if element is not None:
            if not isinstance(element, values.Value):
                element = self.add_metadata(element)  # type: ignore
            if not isinstance(element.type, types.MetaDataType):  # type: ignore
                raise TypeError(
                    "wrong type for metadata element: got {!r}".format(
                        element,
                    )
                )
            nmd.add(element)  # type: ignore
        return nmd  # type: ignore

    def get_named_metadata(self, name: str) -> values.NamedMetaData:
        """
        Return the metadata node with the given *name*.  KeyError is raised
        if no such node exists (contrast with add_named_metadata()).
        """
        return self.namedmetadata[name]

    @property
    def functions(self) -> list[values.Function]:
        """
        A list of functions declared or defined in this module.
        """
        return [v for v in self.globals.values() if isinstance(v, values.Function)]

    @property
    def global_values(self) -> Iterable[values.GlobalVariable]:
        """
        An iterable of global values in this module.
        """
        return self.globals.values()

    def get_global(self, name: str) -> values.GlobalVariable:
        """
        Get a global value by name.
        """
        return self.globals[name]

    def add_global(self, globalvalue: values.GlobalVariable) -> None:
        """
        Add a new global value.
        """
        assert globalvalue.name not in self.globals
        self.globals[globalvalue.name] = globalvalue

    def get_unique_name(self, name: str = "") -> str:
        """
        Get a unique global name with the following *name* hint.
        """
        return self.scope.deduplicate(name)

    def declare_intrinsic(
        self,
        intrinsic: str,
        tys: Sequence[types.Type] = (),
        fnty: types.FunctionType | None = None,
    ) -> values.GlobalVariable | values.Function:
        def _error() -> NoReturn:
            raise NotImplementedError(
                f"unknown intrinsic {intrinsic!r} with {len(tys)} types"
            )

        if intrinsic in {"llvm.cttz", "llvm.ctlz", "llvm.fma"}:
            suffixes: list[str] = [tys[0].intrinsic_name]  # type: ignore
        else:
            suffixes = [t.intrinsic_name for t in tys]  # type: ignore
        name = ".".join([intrinsic] + suffixes)
        if name in self.globals:
            return self.globals[name]

        if fnty is not None:
            # General case: function type is given
            pass
        # Compute function type if omitted for common cases
        elif len(tys) == 0 and intrinsic == "llvm.assume":
            fnty = types.FunctionType(types.VoidType(), [types.IntType(1)])
        elif len(tys) == 1:
            if intrinsic == "llvm.powi":
                fnty = types.FunctionType(tys[0], [tys[0], types.IntType(32)])
            elif intrinsic == "llvm.pow":
                fnty = types.FunctionType(tys[0], tys * 2)  # type: ignore
            elif intrinsic == "llvm.convert.from.fp16":
                fnty = types.FunctionType(tys[0], [types.IntType(16)])
            elif intrinsic == "llvm.convert.to.fp16":
                fnty = types.FunctionType(types.IntType(16), tys)
            else:
                fnty = types.FunctionType(tys[0], tys)
        elif len(tys) == 2:
            if intrinsic == "llvm.memset":
                tys = [tys[0], types.IntType(8), tys[1], types.IntType(1)]
                fnty = types.FunctionType(types.VoidType(), tys)
            elif intrinsic in {"llvm.cttz", "llvm.ctlz"}:
                tys = [tys[0], types.IntType(1)]
                fnty = types.FunctionType(tys[0], tys)
            else:
                _error()
        elif len(tys) == 3:
            if intrinsic in ("llvm.memcpy", "llvm.memmove"):
                tys = tys + [types.IntType(1)]  # type: ignore
                fnty = types.FunctionType(types.VoidType(), tys)
            elif intrinsic == "llvm.fma":
                tys = [tys[0]] * 3
                fnty = types.FunctionType(tys[0], tys)
            else:
                _error()
        else:
            _error()
        return values.Function(self, fnty, name=name)

    def get_identified_types(self) -> dict[str, types.IdentifiedStructType]:
        return self.context.identified_types

    def _get_body_lines(self) -> list[str]:
        # Type declarations
        lines = [it.get_declaration() for it in self.get_identified_types().values()]
        # Global values (including function definitions)
        lines += [str(v) for v in self.globals.values()]
        return lines

    def _get_metadata_lines(self) -> list[str]:
        mdbuf: list[str] = []
        for k, v in self.namedmetadata.items():
            mdbuf.append(
                "!{name} = !{{ {operands} }}".format(
                    name=k,
                    operands=", ".join(i.get_reference() for i in v.operands),
                )
            )
        for md in self.metadata:
            mdbuf.append(str(md))
        return mdbuf

    def _stringify_body(self) -> str:
        # For testing
        return "\n".join(self._get_body_lines())

    def _stringify_metadata(self) -> str:
        # For testing
        return "\n".join(self._get_metadata_lines())

    def __repr__(self) -> str:
        lines: list[str] = []
        # Header
        lines += [
            '; ModuleID = "{}"'.format(
                self.name,
            ),
            'target triple = "{}"'.format(
                self.triple,
            ),
            'target datalayout = "{}"'.format(
                self.data_layout,
            ),
            "",
        ]
        # Body
        lines += self._get_body_lines()
        # Metadata
        lines += self._get_metadata_lines()

        return "\n".join(lines)
