
@rem Let CMake know about the LLVM install path, for find_package()
set CMAKE_PREFIX_PATH=%LIBRARY_PREFIX%
if "%ARCH%"=="32" (
    set CMAKE_GENERATOR_ARCH=
) else (
    set CMAKE_GENERATOR_ARCH=Win64
)
set CMAKE_GENERATOR=Visual Studio 15 2017 %CMAKE_GENERATOR_ARCH%

@rem Ensure there are no build leftovers (CMake can complain)
if exist ffi\build rmdir /S /Q ffi\build

%PYTHON% -S setup.py install
if errorlevel 1 exit 1

%PYTHON% runtests.py
if errorlevel 1 exit 1
