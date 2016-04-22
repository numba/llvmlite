import llvmlite.ir as ll

fntype = ll.FunctionType(ll.IntType(32), [ll.IntType(32), ll.IntType(32)])

module = ll.Module()

func = ll.Function(module, fntype, name='foo')
bb_entry = func.append_basic_block()

builder = ll.IRBuilder()
builder.position_at_end(bb_entry)

stackint = builder.alloca(ll.IntType(32))
builder.store(ll.Constant(stackint.type.pointee, 123), stackint)
myint = builder.load(stackint)

addinstr = builder.add(func.args[0], func.args[1])
mulinstr = builder.mul(addinstr, ll.Constant(ll.IntType(32), 123))
pred = builder.icmp_signed('<', addinstr, mulinstr)
builder.ret(mulinstr)

bb_block = func.append_basic_block()
builder.position_at_end(bb_block)

bb_exit = func.append_basic_block()

pred = builder.trunc(addinstr, ll.IntType(1))
builder.cbranch(pred, bb_block, bb_exit)

builder.position_at_end(bb_exit)
builder.ret(myint)

print(module)
