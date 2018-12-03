mkdir build
cd build

set BUILD_CONFIG=Release

REM Configure step
if "%ARCH%"=="32" (
    set CMAKE_GENERATOR=Visual Studio 14 2015
) else (
    set CMAKE_GENERATOR=Visual Studio 14 2015 Win64
)
set CMAKE_GENERATOR_TOOLSET=v140_xp

REM Reduce build times and package size by removing unused stuff
set CMAKE_CUSTOM=-DLLVM_TARGETS_TO_BUILD=X86 -DLLVM_INCLUDE_TESTS=OFF ^
    -DLLVM_INCLUDE_UTILS=ON -DLLVM_INCLUDE_DOCS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF ^
    -DLLVM_ENABLE_ASSERTIONS=ON -DLLVM_USE_INTEL_JITEVENTS=ON

cmake -G "%CMAKE_GENERATOR%" -T "%CMAKE_GENERATOR_TOOLSET%" ^
    -DCMAKE_BUILD_TYPE="%BUILD_CONFIG%" -DCMAKE_PREFIX_PATH=%LIBRARY_PREFIX% ^
    -DCMAKE_INSTALL_PREFIX:PATH=%LIBRARY_PREFIX% %CMAKE_CUSTOM% %SRC_DIR%
if errorlevel 1 exit 1

REM Build step
cmake --build . --config "%BUILD_CONFIG%"
if errorlevel 1 exit 1

REM Install step
cmake --build . --config "%BUILD_CONFIG%" --target install
if errorlevel 1 exit 1

REM From: https://github.com/conda-forge/llvmdev-feedstock/pull/53
%BUILD_CONFIG%\bin\opt -S -vector-library=SVML -mcpu=haswell -O3 %RECIPE_DIR%\numba-3016.ll | %BUILD_CONFIG%\bin\FileCheck %RECIPE_DIR%\numba-3016.ll
if errorlevel 1 exit 1

REM This is technically how to run the suite, but it will only run in an
REM enhanced unix-like shell which has functions like `grep` available.
REM cd ..\test
REM %PYTHON% ..\build\%BUILD_CONFIG%\bin\llvm-lit.py -vv Transforms ExecutionEngine Analysis CodeGen/X86
REM if errorlevel 1 exit 1
