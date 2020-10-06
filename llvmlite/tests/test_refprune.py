import unittest
from llvmlite import ir
from llvmlite import binding as llvm
from llvmlite.tests import TestCase

from . import refprune_proto as proto


def _iterate_cases(generate_test):
    def wrap(fn):
        def wrapped(self):
            return generate_test(self, fn)
        wrapped.__doc__ = f"generated test for {fn.__module__}.{fn.__name__}"
        return wrapped

    for k, case_fn in proto.__dict__.items():
        if k.startswith('case'):
            yield f'test_{k}', wrap(case_fn)


class TestRefPrunePrototype(TestCase):
    """
    Test that the prototype is working.
    """
    def generate_test(self, case_gen):
        nodes, edges, expected = case_gen()
        got = proto.FanoutAlgorithm(nodes, edges).run()
        self.assertEqual(expected, got)

    # Generate tests
    for name, case in _iterate_cases(generate_test):
        locals()[name] = case


ptr_ty = ir.IntType(8).as_pointer()


class TestRefPrunePass(TestCase):
    """
    Test that the C++ implementation matches the expected behavior as for
    the prototype.

    This generates a LLVM module for each test case, runs the pruner and check
    that the expected results are achieved.
    """

    def make_incref(self, m):
        fnty = ir.FunctionType(ir.VoidType(), [ptr_ty])
        return ir.Function(m, fnty, name='NRT_incref')

    def make_decref(self, m):
        fnty = ir.FunctionType(ir.VoidType(), [ptr_ty])
        return ir.Function(m, fnty, name='NRT_decref')

    def make_switcher(self, m):
        fnty = ir.FunctionType(ir.IntType(32), ())
        return ir.Function(m, fnty, name='switcher')

    def make_brancher(self, m):
        fnty = ir.FunctionType(ir.IntType(1), ())
        return ir.Function(m, fnty, name='brancher')

    def generate_ir(self, nodes, edges):
        # Build LLVM module for the CFG
        m = ir.Module()

        incref_fn = self.make_incref(m)
        decref_fn = self.make_decref(m)
        switcher_fn = self.make_switcher(m)
        brancher_fn = self.make_brancher(m)

        fnty = ir.FunctionType(ir.VoidType(), [ptr_ty])
        fn = ir.Function(m, fnty, name='main')
        [ptr] = fn.args
        ptr.name = 'mem'
        # populate the BB nodes
        bbmap = {}
        for bb in edges:
            bbmap[bb] = fn.append_basic_block(bb)
        # populate the edges
        builder = ir.IRBuilder()
        for bb, jump_targets in edges.items():
            builder.position_at_end(bbmap[bb])
            for action in nodes[bb]:
                if action == 'incref':
                    builder.call(incref_fn, [ptr])
                elif action == 'decref':
                    builder.call(decref_fn, [ptr])
                else:
                    raise AssertionError('unreachable')

            n_targets = len(jump_targets)
            if n_targets == 0:
                builder.ret_void()
            elif n_targets == 1:
                [dst] = jump_targets
                builder.branch(bbmap[dst])
            elif n_targets == 2:
                [left, right] = jump_targets
                sel = builder.call(brancher_fn, ())
                builder.cbranch(sel, bbmap[left], bbmap[right])
            elif n_targets > 2:
                sel = builder.call(switcher_fn, ())
                [head, *tail] = jump_targets

                sw = builder.switch(sel, default=bbmap[head])
                for i, dst in enumerate(tail):
                    sw.add_case(sel.type(i), bbmap[dst])
            else:
                raise AssertionError('unreachable')

        return m

    def apply_refprune(self, irmod):
        mod = llvm.parse_assembly(str(irmod))
        pm = llvm.ModulePassManager()
        pm.add_refprune_pass()
        pm.run(mod)
        return mod

    def check(self, mod, expected, nodes):
        # preprocess incref/decref locations
        d = {}
        for k, vs in nodes.items():
            n_incref = vs.count('incref')
            n_decref = vs.count('decref')
            d[k] = {'incref': n_incref, 'decref': n_decref}
        for k, stats in d.items():
            if expected.get(k):
                stats['incref'] -= 1
                for dec_bb in expected[k]:
                    d[dec_bb]['decref'] -= 1

        # find the main function
        for f in mod.functions:
            if f.name == 'main':
                break
        # check each BB
        for bb in f.blocks:
            stats = d[bb.name]
            text = str(bb)
            n_incref = text.count('NRT_incref')
            n_decref = text.count('NRT_decref')
            self.assertEqual(stats['incref'], n_incref, msg=f'BB {bb}')
            self.assertEqual(stats['decref'], n_decref, msg=f'BB {bb}')

    def generate_test(self, case_gen):
        nodes, edges, expected = case_gen()
        irmod = self.generate_ir(nodes, edges)
        outmod = self.apply_refprune(irmod)
        self.check(outmod, expected, nodes)

    # Generate tests
    for name, case in _iterate_cases(generate_test):
        locals()[name] = case


if __name__ == '__main__':
    unittest.main()
