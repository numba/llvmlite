# file name can vary
try:
    # llvm 7 name
    with open("cfg.testme.dot") as fin:
        got = fin.read()
except IOError:
    # llvm 8 name
    with open(".testme.dot") as fin:
        got = fin.read()

assert '[label="W:1"]' in got
assert '[label="W:9"]' in got
