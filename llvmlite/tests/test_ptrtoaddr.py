import unittest
from llvmlite import ir, ir_layer_typed_pointers_enabled


class TestPtrToAddr(unittest.TestCase):
    def test_builder_ptrtoaddr(self):
        mod = ir.Module(name="test_mod")
        arg_ty = ir.IntType(32).as_pointer()
        func_ty = ir.FunctionType(ir.IntType(64), [arg_ty])
        func = ir.Function(mod, func_ty, name="ptr_to_addr_fn")
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        ptr_arg = func.args[0]
        addr = builder.ptrtoaddr(ptr_arg, ir.IntType(64), name="addr")
        builder.ret(addr)

        ir_output = str(mod)
        if not ir_layer_typed_pointers_enabled:
            self.assertIn('ptrtoaddr ptr %".1" to i64', ir_output)
        else:
            self.assertIn('ptrtoaddr i32* %".1" to i64', ir_output)

    def test_constant_ptrtoaddr_null(self):
        ptr = ir.Constant(ir.IntType(64).as_pointer(), None)
        c = ptr.ptrtoaddr(ir.IntType(32))
        if not ir_layer_typed_pointers_enabled:
            self.assertEqual(str(c), "ptrtoaddr (ptr null to i32)")
        else:
            self.assertEqual(str(c), "ptrtoaddr (i64* null to i32)")

    def test_constant_ptrtoaddr_global(self):
        mod = ir.Module(name="test_mod")
        gv = ir.GlobalVariable(mod, ir.IntType(32), "my_global")
        c = gv.ptrtoaddr(ir.IntType(64))
        if not ir_layer_typed_pointers_enabled:
            self.assertEqual(str(c), 'ptrtoaddr (ptr @"my_global" to i64)')
        else:
            self.assertEqual(str(c), 'ptrtoaddr (i32* @"my_global" to i64)')

    def test_constant_ptrtoaddr_type_errors(self):
        one = ir.Constant(ir.IntType(32), 1)
        int64 = ir.IntType(64)
        flt = ir.FloatType()
        ptr = ir.Constant(int64.as_pointer(), None)

        # Calling ptrtoaddr on non-pointer
        with self.assertRaises(TypeError) as ctx:
            one.ptrtoaddr(int64)
        msg = "can only call ptrtoaddr() on pointer type"
        self.assertIn(msg, str(ctx.exception))

        # Casting to non-integer type
        with self.assertRaises(TypeError) as ctx:
            ptr.ptrtoaddr(flt)
        msg = "can only ptrtoaddr() to integer type"
        self.assertIn(msg, str(ctx.exception))

    def test_builder_ptrtoaddr_same_type_noop(self):
        # When value already has target type, _castop returns value directly
        mod = ir.Module(name="test_mod")
        func_ty = ir.FunctionType(ir.IntType(64), [ir.IntType(64)])
        func = ir.Function(mod, func_ty, name="noop_fn")
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        val = func.args[0]
        res = builder.ptrtoaddr(val, ir.IntType(64))
        self.assertIs(res, val)


if __name__ == "__main__":
    unittest.main()
