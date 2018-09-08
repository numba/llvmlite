try:
    from setuptools import setup, Extension
    # Required for compatibility with pip (issue #177)
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup, Extension
    from distutils.command.install import install


try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

from distutils.command.build import build
from distutils.command.build_ext import build_ext
from distutils.command.clean import clean
from distutils import log
from distutils.dir_util import remove_tree
from distutils.spawn import spawn
import os
import sys
import shutil

if os.environ.get('READTHEDOCS', None) == 'True':
    sys.exit("setup.py disabled on readthedocs: called with %s"
             % (sys.argv,))

import versioneer

versioneer.VCS = 'git'
versioneer.versionfile_source = 'llvmlite/_version.py'
versioneer.versionfile_build = 'llvmlite/_version.py'
versioneer.tag_prefix = 'v' # tags are like v1.2.0
versioneer.parentdir_prefix = 'llvmlite-' # dirname like 'myproject-1.2.0'


here_dir = os.path.dirname(os.path.abspath(__file__))

cmdclass = versioneer.get_cmdclass()
build = cmdclass.get('build', build)
build_ext = cmdclass.get('build_ext', build_ext)


def build_library_files(dry_run):
    cmd = [sys.executable, os.path.join(here_dir, 'ffi', 'build.py')]
    spawn(cmd, dry_run=dry_run)


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
        build_library_files(self.dry_run)
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

class LlvmliteClean(clean):
    """Custom clean command to tidy up the project root."""
    def run(self):
        clean.run(self)
        path = os.path.join(here_dir, 'llvmlite.egg-info')
        if os.path.isdir(path):
            remove_tree(path, dry_run=self.dry_run)
        if not self.dry_run:
            self._rm_walk()

    def _rm_walk(self):
        for path, dirs, files in os.walk(here_dir):
            if any(p.startswith('.') for p in path.split(os.path.sep)):
                # Skip hidden directories like the git folder right away
                continue
            if path.endswith('__pycache__'):
                remove_tree(path, dry_run=self.dry_run)
            else:
                for fname in files:
                    if fname.endswith('.pyc') or fname.endswith('.so'):
                        fpath = os.path.join(path, fname)
                        os.remove(fpath)
                        log.info("removing '%s'", fpath)


if bdist_wheel:
    class LLvmliteBDistWheel(bdist_wheel):
        def run(self):
            # Ensure the binding file exist when running wheel build
            from llvmlite.utils import get_library_files
            build_library_files(self.dry_run)
            self.distribution.package_data.update({
                "llvmlite.binding": get_library_files(),
            })
            # Run wheel build command
            bdist_wheel.run(self)

        def finalize_options(self):
            bdist_wheel.finalize_options(self)
            # The build isn't platform-independent
            self.root_is_pure = False


cmdclass.update({'build': LlvmliteBuild,
                 'build_ext': LlvmliteBuildExt,
                 'install': LlvmliteInstall,
                 'clean': LlvmliteClean,
                 })

if bdist_wheel:
    cmdclass.update({'bdist_wheel': LLvmliteBDistWheel})

# A stub C-extension to make bdist_wheel build an arch dependent build
ext_stub = Extension(name="llvmlite.binding._stub",
                     sources=["llvmlite/binding/_stub.c"])


packages = ['llvmlite',
            'llvmlite.binding',
            'llvmlite.ir',
            'llvmlite.llvmpy',
            'llvmlite.tests',
            ]

install_requires = []
setup_requires = []
if sys.version_info < (3, 4):
    install_requires.append('enum34')
    setup_requires.append('enum34')


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
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
      ],
      # Include the separately-compiled shared library
      author="Continuum Analytics, Inc.",
      author_email="numba-users@continuum.io",
      url="http://llvmlite.pydata.org",
      download_url="https://github.com/numba/llvmlite",
      packages=packages,
      install_requires=install_requires,
      setup_requires=setup_requires,
      license="BSD",
      cmdclass=cmdclass,
      long_description=long_description,
      )
