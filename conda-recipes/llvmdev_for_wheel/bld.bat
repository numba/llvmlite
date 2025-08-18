REM base on https://github.com/AnacondaRecipes/llvmdev-feedstock/blob/master/recipe/bld.bat
echo on

REM First, setup the VS2022 environment
for /F "usebackq tokens=*" %%i in (`vswhere.exe -nologo -products * -version "[17.0,18.0)" -property installationPath`) do (
  set "VSINSTALLDIR=%%i\\"
)
if not exist "%VSINSTALLDIR%" (
  echo "Could not find VS 2022"
  exit /B 1
)

echo "Found VS 2022 in %VSINSTALLDIR%"
call "%VSINSTALLDIR%VC\\Auxiliary\\Build\\vcvarsall.bat" x64

mkdir build
cd build

REM remove GL flag for now
set "CXXFLAGS=-MD"
set "CC=cl.exe"
set "CXX=cl.exe"

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
    -DLLVM_ENABLE_PROJECTS:STRING=lld;compiler-rt ^
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
