from __future__ import annotations

from llvmlite.ir import CallInstr
from llvmlite.ir.instructions import Instruction
from llvmlite.ir.module import Module
from llvmlite.ir.values import Block, Function


class Visitor:
    def visit(self, module: Module) -> None:
        self._module = module
        for func in module.functions:
            self.visit_Function(func)

    def visit_Function(self, func: Function) -> None:
        self._function = func
        for bb in func.blocks:
            self.visit_BasicBlock(bb)

    def visit_BasicBlock(self, bb: Block) -> None:
        self._basic_block = bb
        for instr in bb.instructions:
            self.visit_Instruction(instr)

    def visit_Instruction(self, instr: Instruction) -> None:
        raise NotImplementedError

    @property
    def module(self) -> Module:
        return self._module

    @property
    def function(self) -> Function:
        return self._function

    @property
    def basic_block(self) -> Block:
        return self._basic_block


class CallVisitor(Visitor):
    def visit_Instruction(self, instr: Instruction) -> None:
        if isinstance(instr, CallInstr):
            self.visit_Call(instr)

    def visit_Call(self, instr: CallInstr) -> None:
        raise NotImplementedError


class ReplaceCalls(CallVisitor):
    def __init__(self, orig: Function, repl: Function) -> None:
        super().__init__()
        self.orig = orig
        self.repl = repl
        self.calls: list[CallInstr] = []

    def visit_Call(self, instr: CallInstr) -> None:
        if instr.callee == self.orig:
            instr.replace_callee(self.repl)
            self.calls.append(instr)


def replace_all_calls(mod: Module, orig: Function, repl: Function) -> list[CallInstr]:
    """Replace all calls to `orig` to `repl` in module `mod`.
    Returns the references to the returned calls
    """
    rc = ReplaceCalls(orig, repl)
    rc.visit(mod)
    return rc.calls
