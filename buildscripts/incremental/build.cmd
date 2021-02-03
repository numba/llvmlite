
call activate %CONDA_ENV%

python setup.py build
python setup.py bdist_wheel
