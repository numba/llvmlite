from setuptools import setup, Command, Extension
from setuptools.command.build import build
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install
from shutil import rmtree
from subprocess import run
import logging
import os
import sys

import versioneer

logger = logging.getLogger(__name__)


try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

min_python_version = (3, 10)


def _version_info_str(int_tuple):
    return ".".join(map(str, int_tuple))


def _guard_py_ver():
    current_python_version = sys.version_info[:3]
    min_py = _version_info_str(min_python_version)
    cur_py = _version_info_str(current_python_version)

    if not min_python_version <= current_python_version:
        msg = ('Cannot install on Python version {}; only versions >={} '
               'are supported.')
        raise RuntimeError(msg.format(cur_py, min_py))


_guard_py_ver()

versioneer.VCS = 'git'
versioneer.versionfile_source = 'llvmlite/_version.py'
versioneer.versionfile_build = 'llvmlite/_version.py'
versioneer.tag_prefix = 'v' # tags are like v1.2.0
versioneer.parentdir_prefix = 'llvmlite-' # dirname like 'myproject-1.2.0'


here_dir = os.path.dirname(os.path.abspath(__file__))

cmdclass = versioneer.get_cmdclass()
build = cmdclass.get('build', build)
build_ext = cmdclass.get('build_ext', build_ext)


def build_library_files():
    cmd = [sys.executable, os.path.join(here_dir, 'ffi', 'build.py')]
    # Turn on -fPIC for building on Linux, BSD, OS X, and GNU platforms
    plt = sys.platform
    if 'linux' in plt or 'bsd' in plt or 'darwin' in plt or 'gnu' in plt:
        os.environ['CXXFLAGS'] = os.environ.get('CXXFLAGS', '') + ' -fPIC'

    run(cmd, check=True)


class LlvmliteBuild(build):
    def finalize_options(self):
        build.finalize_options(self)
        # The build isn't platform-independent
        if self.build_lib == self.build_purelib:
            self.build_lib = self.build_platlib

    def get_sub_commands(self):
        # Force "build_ext" invocation.
        commands = build.get_sub_commands(self)
        for c in commands:
            if c == 'build_ext':
                return commands
        return ['build_ext'] + commands


class LlvmliteBuildExt(build_ext):

    def run(self):
        build_ext.run(self)
        build_library_files()
        # HACK: this makes sure the library file (which is large) is only
        # included in binary builds, not source builds.
        from llvmlite.utils import get_library_files
        self.distribution.package_data = {
            "llvmlite.binding": get_library_files(),
        }


class LlvmliteInstall(install):
    # Ensure install see the libllvmlite shared library
    # This seems to only be necessary on OSX.
    def run(self):
        from llvmlite.utils import get_library_files
        self.distribution.package_data = {
            "llvmlite.binding": get_library_files(),
        }
        install.run(self)

    def finalize_options(self):
        install.finalize_options(self)
        # Force use of "platlib" dir for auditwheel to recognize this
        # is a non-pure build
        self.install_libbase = self.install_platlib
        self.install_lib = self.install_platlib


class LlvmliteClean(Command):
    """Custom clean command to tidy up the project root."""
    # Required to implement but there don't appear to be any relevant flags
    # for this command, so do nothing
    def initialize_options(self) -> None:
        pass

    # Required to implement but there don't appear to be any relevant flags
    # for this command, so do nothing
    def finalize_options(self) -> None:
        pass

    def run(self):
        build_dir = os.path.join(here_dir, 'build')
        if os.path.exists(build_dir):
            self._rm_tree(build_dir)
        path = os.path.join(here_dir, 'llvmlite.egg-info')
        if os.path.isdir(path):
            self._rm_tree(path)
        ffi_build = os.path.join(here_dir, 'ffi', 'build')
        if os.path.exists(ffi_build):
            self._rm_tree(ffi_build)
        # restrict rm_walk here to llvmlite dir to avoid touching other
        # subdirectories; build/ and ffi/build/ are
        # already removed above via _rm_tree.
        self._rm_walk(os.path.join(here_dir, 'llvmlite'))

    def _rm_walk(self, root):
        for path, _, files in os.walk(root):
            if any(p.startswith('.') for p in path.split(os.path.sep)):
                # Skip hidden directories like the git folder right away
                continue
            if path.endswith('__pycache__'):
                self._rm_tree(path)
            else:
                for fname in files:
                    suffixes = ('.pyc', '.o', '.so', '.dylib', '.dll')
                    if any(fname.endswith(suffix) for suffix in suffixes):
                        fpath = os.path.join(path, fname)
                        os.remove(fpath)
                        logger.info("removing '%s'", fpath)

    def _rm_tree(self, path):
        logger.info("removing '%s' (and everything underneath it)", path)
        rmtree(path)


cmdclass.update({'build': LlvmliteBuild,
                 'build_ext': LlvmliteBuildExt,
                 'install': LlvmliteInstall,
                 'clean': LlvmliteClean,
                 })

if bdist_wheel is not None:
    class LLvmliteBDistWheel(bdist_wheel):
        def run(self):
            # Ensure the binding file exist when running wheel build
            from llvmlite.utils import get_library_files
            build_library_files()
            self.distribution.package_data.update({
                "llvmlite.binding": get_library_files(),
            })
            # Run wheel build command
            bdist_wheel.run(self)

        def finalize_options(self):
            bdist_wheel.finalize_options(self)
            # The build isn't platform-independent
            self.root_is_pure = False

    cmdclass.update({'bdist_wheel': LLvmliteBDistWheel})

# A stub C-extension to make bdist_wheel build an arch dependent build
ext_stub = Extension(name="llvmlite.binding._stub",
                     sources=["llvmlite/binding/_stub.c"])


packages = ['llvmlite',
            'llvmlite.binding',
            'llvmlite.ir',
            'llvmlite.tests',
            ]


with open('README.rst') as f:
    long_description = f.read()


setup(name='llvmlite',
      description="lightweight wrapper around basic LLVM functionality",
      version=versioneer.get_version(),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.10",
          "Programming Language :: Python :: 3.11",
          "Programming Language :: Python :: 3.12",
          "Programming Language :: Python :: 3.13",
          "Programming Language :: Python :: 3.14",
          "Topic :: Software Development :: Code Generators",
          "Topic :: Software Development :: Compilers",
      ],
      # Include the separately-compiled shared library
      url="http://llvmlite.readthedocs.io",
      project_urls={
          "Source": "https://github.com/numba/llvmlite",
      },
      packages=packages,
      license_expression="BSD-2-Clause AND Apache-2.0 WITH LLVM-exception",
      license_files=['LICENSE', 'LICENSE.thirdparty'],
      cmdclass=cmdclass,
      long_description=long_description,
      python_requires=">={}".format(_version_info_str(min_python_version)),
      )
