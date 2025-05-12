
call activate %CONDA_ENV%

if "%OPAQUE_POINTERS%"=="yes" (
  set LLVMLITE_ENABLE_IR_LAYER_TYPED_POINTERS=0
  echo "Testing with IR layer opaque pointers enabled"
) else (
  echo "Testing with IR layer opaque pointers disabled"
)

python runtests.py -v
