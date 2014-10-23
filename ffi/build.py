
import os
import subprocess
import shutil
import sys


here_dir = os.path.abspath(os.path.dirname(__file__))
build_dir = os.path.join(here_dir, 'build')


def main_win32():
    # NOTE: the LLVM build must have the same bitness as the Python runtime.
    # I don't know if there's an way for us to check this.
    config = 'Release'
    if not os.path.isdir(build_dir):
        os.mkdir(build_dir)
    os.chdir(build_dir)
    subprocess.check_call(['cmake', here_dir])
    subprocess.check_call(['cmake', '--build', '.', '--config', config])
    shutil.copy(os.path.join(build_dir, config, 'llvmlite.dll'), here_dir)


def main():
    if sys.platform == 'win32':
        main_win32()
    elif sys.platform.startswith('linux'):
        main_posix('linux')
    elif sys.platform == 'darwin':
        main_posix('osx')
    else:
        raise RuntimeError("unsupported platform: %r" % (sys.platform,))


if __name__ == "__main__":
    main()
