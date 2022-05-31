import math

from llvmlite.ir import Constant, DoubleType, FloatType

print(Constant(FloatType(), math.pi))
print(Constant(DoubleType(), math.pi))
print(Constant(FloatType(), float("+inf")))
print(Constant(DoubleType(), float("+inf")))
print(Constant(FloatType(), float("-inf")))
print(Constant(DoubleType(), float("-inf")))
