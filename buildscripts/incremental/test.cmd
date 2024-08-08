
call activate %CONDA_ENV%

if "%OPAQUE_POINTERS%"=="yes" (
  set LLVMLITE_ENABLE_OPAQUE_POINTERS=1
  echo "Testing with opaque pointers enabled"
) else (
  echo "Testing with opaque pointers disabled"
)

python runtests.py -v
