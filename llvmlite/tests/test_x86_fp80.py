"""Tests for the x86_fp80 IR type (no target-specific code generation)."""

import pickle
import unittest

from llvmlite import binding as llvm
from llvmlite import ir


class TestX86FP80Type(unittest.TestCase):
    def test_type_identity(self):
        ty = ir.X86FP80Type()
        self.assertIs(ty, ir.X86FP80Type())
        self.assertEqual(str(ty), 'x86_fp80')
        self.assertEqual(ty.intrinsic_name, 'f80')
        self.assertNotEqual(ty, ir.DoubleType())
        self.assertEqual(hash(ty), hash(ir.X86FP80Type()))
        self.assertIs(pickle.loads(pickle.dumps(ty)), ty)

    def test_constants(self):
        ty = ir.X86FP80Type()
        self.assertEqual(str(ir.Constant(ty, None)),
                         'x86_fp80 zeroinitializer')
        self.assertEqual(str(ir.Constant(ty, '0xK3FFF8000000000000000')),
                         'x86_fp80 0xK3FFF8000000000000000')
        for value in [0, 1.0, '0.0', '0xK123', '0xK' + 'Z' * 20]:
            with self.subTest(value=value), self.assertRaises(TypeError):
                str(ir.Constant(ty, value))

        mod = ir.Module()
        var = ir.GlobalVariable(mod, ty, 'one')
        var.initializer = ir.Constant(ty, '0xK3FFF8000000000000000')
        zero = ir.GlobalVariable(mod, ty, 'zero')
        zero.initializer = ir.Constant(ty, None)
        llmod = llvm.parse_assembly(str(mod))
        llmod.verify()

    def test_arithmetic_and_casts(self):
        ty = ir.X86FP80Type()
        mod = ir.Module()
        fnty = ir.FunctionType(ty, [ty, ty, ir.DoubleType()])
        fn = ir.Function(mod, fnty, name='compute')
        builder = ir.IRBuilder(fn.append_basic_block('entry'))
        a, b, d = fn.args
        add = builder.fadd(a, b)
        sub = builder.fsub(add, b)
        mul = builder.fmul(sub, a)
        div = builder.fdiv(mul, b)
        cmp = builder.fcmp_ordered('<', div, b)
        narrowed = builder.fptrunc(div, ir.DoubleType())
        widened = builder.fpext(narrowed, ty)
        selected = builder.select(cmp, widened, builder.fpext(d, ty))
        builder.ret(selected)

        ir_text = str(mod)
        for op in ('fadd', 'fsub', 'fmul', 'fdiv', 'fcmp', 'fptrunc', 'fpext'):
            self.assertIn(op, ir_text)
        llmod = llvm.parse_assembly(ir_text)
        llmod.verify()

        typeref = llmod.get_function('compute').global_value_type
        self.assertEqual(typeref.type_kind, llvm.TypeKind.function)
        self.assertIs(typeref.get_function_return().as_ir(ir.Context()), ty)
        paramty = typeref.get_function_parameters()
        self.assertIs(paramty[0].as_ir(ir.Context()), ty)
        self.assertIs(paramty[1].as_ir(ir.Context()), ty)
        self.assertIsInstance(paramty[2].as_ir(ir.Context()), ir.DoubleType)

    def test_aggregate_type_roundtrip(self):
        ty = ir.X86FP80Type()
        arr = ir.ArrayType(ty, 3)
        mod = ir.Module()
        ir.GlobalVariable(mod, arr, 'values')
        llmod = llvm.parse_assembly(str(mod))
        llmod.verify()
        typeref = llmod.get_global_variable('values').global_value_type
        self.assertEqual(typeref.as_ir(ir.Context()), arr)
        self.assertIs(next(iter(typeref.elements)).as_ir(ir.Context()), ty)


if __name__ == '__main__':
    unittest.main()
