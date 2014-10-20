from llvmlite.ir import Constant, FloatType, DoubleType
import math

print(Constant(FloatType(), math.pi))
print(Constant(DoubleType(), math.pi))
print(Constant(FloatType(), float('+inf')))
print(Constant(DoubleType(), float('+inf')))
print(Constant(FloatType(), float('-inf')))
print(Constant(DoubleType(), float('-inf')))
