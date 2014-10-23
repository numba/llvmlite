try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

from distutils.spawn import spawn
from distutils.command.build import build
import os
import sys

from llvmlite.utils import get_library_name


here_dir = os.path.dirname(__file__)


class LlvmliteBuild(build):

    def run(self):
        cmd = [sys.executable, os.path.join(here_dir, 'ffi', 'build.py')]
        spawn(cmd, dry_run=self.dry_run)


packages = ['llvmlite',
            'llvmlite.binding',
            'llvmlite.llvmpy',
            'llvmlite.tests',
            ]

setup(name='llvmlite',
      description="lightweight wrapper around basic LLVM functionality",

      classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
      ],
      # Include the separately-compiled shared library
      package_data={
          "llvmlite.binding": [get_library_name()],
      },
      author="Continuum Analytics, Inc.",
      author_email="numba-users@continuum.io",
      url="https://github.com/numba/llvmlite",
      packages=packages,
      license="BSD",
      cmdclass={'build': LlvmliteBuild},
      )
