Notes on building from source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The software involved is as follows:

* Numba is the compiler package, it depends on `llvmlite`.
* llvmlite is a binding package to the LLVM APIs, it depends on LLVM.
* LLVM is the JIT compiler framework for producing executable code from various
  inputs.


Conda packages:
~~~~~~~~~~~~~~~

The Numba maintainers ship to the Numba channel:
  * Numba packages
  * llvmlite packages
  * llvmdev packages (this contains a build of LLVM)

The llvmdev packages are not needed at runtime by llvmlite packages as
llvmlite's dynamic libraries are statically linked at compile time against LLVM
through the dependency on the `llvmdev` package.

The Anaconda distribution and conda-forge channels ship:
  * Numba packages
  * llvmlite packages
  * LLVM split into runtime libraries (package called `llvm`) and compile time
    libraries/headers etc this contains a build of LLVM (package called
    `llvmdev`)

At compile time the `llvmdev` and `llvm` packages are used to build llvmlite and
llvmlite's dynamic libraries are dynamically linked against the libraries in the
`llvm` meta-package. This means at runtime `llvmlite` depends on the `llvm`
package which has the LLVM shared libraries in it (it's actually a package
called `libllvm` that contains the DSOs, but the `llvm` package is referred to
so as to get the `run_exports`).

Using `pip`
~~~~~~~~~~~

The Numba maintainers ship binary wheels:

  * Numba wheels (x86* architectures)
  * llvmlite wheels (x86* architectures)

Note that the llvmlite wheels are statically linked against LLVM, as per the
conda packages on the Numba channel. This mitigates the need for a LLVM based
binary wheel.

The Numba maintainers ship an `sdist` for:

  * Numba
  * llvmlite

Note that there is no `sdist` provided for LLVM. If you try and build `llvmlite`
from `sdist` you will need to bootstrap the package with your own appropriate
LLVM.

How this ends up being a problem.

1. If you are on an unsupported architecture (i.e. not x86*) or unsupported
   python version for binary wheels (e.g. python alphas) then `pip` will try and
   build Numba from `sdist` which in turn will try and build `llvmlite` from
   `sdist`. This will inevitably fail as the `llvmlite` source distribution
   needs an appropriate LLVM installation to build.
2. If you are using `pip` version `< 19.0` then `manylinux2010` wheels will not
   install and you end up in the situation in 1. i.e. something unsupported so
   building from `sdist`.

Things to "fix" it...

1. If you are using pip < 19.0 and on x86*, then update it if you can, this will
   let you use the binary wheels.
2. If you are on an unsupported architecture or using an unsupported python, you
   will probably need to build from source, this means providing an LLVM. If you
   have conda available you could use this to bootstrap the installation with a
   working `llvm`/`llvmdev` package. If you have a system LLVM that's of an
   appropriate version you could use that. See https://llvmlite.readthedocs.io/en/latest/admin-guide/install.html#building-manually
   and in particular note the use of the ``LLVM_CONFIG`` environment variable
   for specifying where your LLVM install is.
3. Use `conda`.
