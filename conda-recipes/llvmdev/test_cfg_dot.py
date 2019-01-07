with open("cfg.testme.dot") as fin:
    got = fin.read()

assert '[label="W:1"]' in got
assert '[label="W:9"]' in got
