REM base on https://github.com/AnacondaRecipes/llvmdev-feedstock/blob/master/recipe/bld.bat
echo on

REM First, setup the VS environment (VS2022 or VS2026)
for /F "usebackq tokens=*" %%i in (`vswhere.exe -nologo -products * -version "[17.0,19.0)" -property installationPath`) do (
  set "VSINSTALLDIR=%%i\\"
)
if not exist "%VSINSTALLDIR%" (
  echo "Could not find VS 2022 or VS 2026"
  exit /B 1
)

echo "Found VS in %VSINSTALLDIR%"

REM ARCH is set by conda-build (e.g., "64" for x64, "arm64" for ARM64)
if "%ARCH%"=="arm64" (
    set "VCVARS_ARCH=arm64"
) else (
    set "VCVARS_ARCH=x64"
)

echo "Building for architecture: %VCVARS_ARCH%"
REM Pin MSVC v14.44 (v143): the vs2022 activation package and llvmlite's
REM link step are v14.44; VS2026 would otherwise default to v14.5x, and
REM v14.5x objects cannot be linked by a v14.44 toolset.
call "%VSINSTALLDIR%VC\\Auxiliary\\Build\\vcvarsall.bat" %VCVARS_ARCH% -vcvars_ver=14.44

mkdir build
cd build

REM remove GL flag for now
set "CXXFLAGS=-MD"
set "CC=cl.exe"
set "CXX=cl.exe"

if "%ARCH%"=="arm64" (
    REM compiler-rt excluded for win-arm64 (as of 2026-06-03):
    REM Build fails in aarch64/fp_mode.c and cpu_model/aarch64.c with MSVC
    set "LLVM_ENABLE_PROJECTS=lld"
) else (
    set "LLVM_ENABLE_PROJECTS=lld;compiler-rt"
)

cmake -G "Ninja" ^
    -DCMAKE_BUILD_TYPE="Release" ^
    -DCMAKE_PREFIX_PATH=%LIBRARY_PREFIX% ^
    -DCMAKE_INSTALL_PREFIX:PATH=%LIBRARY_PREFIX% ^
    -DLLVM_USE_INTEL_JITEVENTS=ON ^
    -DLLVM_ENABLE_LIBXML2=OFF ^
    -DLLVM_ENABLE_RTTI=OFF ^
    -DLLVM_ENABLE_ZLIB=OFF ^
    -DLLVM_ENABLE_ZSTD=OFF ^
    -DLLVM_INCLUDE_BENCHMARKS=OFF ^
    -DLLVM_INCLUDE_DOCS=OFF ^
    -DLLVM_INCLUDE_EXAMPLES=OFF ^
    -DLLVM_INCLUDE_TESTS=ON ^
    -DLLVM_INCLUDE_UTILS=ON ^
    -DLLVM_INSTALL_UTILS=ON ^
    -DLLVM_UTILS_INSTALL_DIR=libexec\llvm ^
    -DLLVM_BUILD_LLVM_C_DYLIB=no ^
    -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly ^
    -DCMAKE_POLICY_DEFAULT_CMP0111=NEW ^
    -DLLVM_ENABLE_PROJECTS:STRING=%LLVM_ENABLE_PROJECTS% ^
    -DLLVM_ENABLE_ASSERTIONS=ON ^
    -DLLVM_ENABLE_DIA_SDK=OFF ^
    -DCOMPILER_RT_BUILD_BUILTINS=ON ^
    -DCOMPILER_RT_BUILTINS_HIDE_SYMBOLS=OFF ^
    -DCOMPILER_RT_BUILD_LIBFUZZER=OFF ^
    -DCOMPILER_RT_BUILD_CRT=OFF ^
    -DCOMPILER_RT_BUILD_MEMPROF=OFF ^
    -DCOMPILER_RT_BUILD_PROFILE=OFF ^
    -DCOMPILER_RT_BUILD_SANITIZERS=OFF ^
    -DCOMPILER_RT_BUILD_XRAY=OFF ^
    -DCOMPILER_RT_BUILD_GWP_ASAN=OFF ^
    -DCOMPILER_RT_BUILD_ORC=OFF ^
    -DCOMPILER_RT_INCLUDE_TESTS=OFF ^
    %SRC_DIR%/llvm
if %ERRORLEVEL% neq 0 exit 1

cmake --build .
if %ERRORLEVEL% neq 0 exit 1

cmake --build . --target install

if %ERRORLEVEL% neq 0 exit 1

REM bin\opt -S -vector-library=SVML -mcpu=haswell -O3 %RECIPE_DIR%\numba-3016.ll | bin\FileCheck %RECIPE_DIR%\numba-3016.ll
REM if %ERRORLEVEL% neq 0 exit 1

cd ..\llvm\test
python ..\..\build\bin\llvm-lit.py -vv Transforms ExecutionEngine Analysis CodeGen/X86
