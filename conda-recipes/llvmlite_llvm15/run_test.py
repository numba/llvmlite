import os
from llvmlite.tests import main

# Enable tests for distribution only
os.environ['LLVMLITE_DIST_TEST'] = '1'
main()
