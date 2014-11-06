
@rem Let CMake know about the LLVM install path, for find_package()
set CMAKE_PREFIX_PATH=%LIBRARY_PREFIX%

python -S setup.py install
if errorlevel 1 exit 1
