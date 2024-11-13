# README: Building manylinux Wheels


## Build llvmdev packages for manylinux

Run the script below to start docker off building `llvmdev` base from the current state of the source tree:

- 64-bit linux: `./buildscripts/manylinux/docker_run_x64.sh build_llvmdev.sh`
    - uses manylinux2014 image for glibc 2.17+
- aarch64 linux: `./buildscripts/manylinux/docker_run_aarch64.sh build_llvmdev.sh`
    - uses manylinux_2_28 image for glibc 2.28+

The conda packages will be stored into `<llvmlite_source_root>/docker_output`

Note: the `docker_output` location can be used as a local conda channel.

Finally, upload the conda package to the numba channel under the "manylinux_x_y" label:

`anaconda upload -u numba -l manylinux_x_y <filepath>`


## Build llvmlite wheel for manylinux

Run the script below to start docker off building `llvmlite` base from the current state of the source tree:

- 32-bit linux: `./buildscripts/manylinux/docker_run_x32.sh build_llvmlite.sh <pyver>`
- 64-bit linux: `./buildscripts/manylinux/docker_run_x64.sh build_llvmlite.sh <pyver>`

The conda packages will be stored into `<llvmlite_source_root>/docker_output/dist_<arch>_<pyver>`

Available Python installations (`<pyver>`) are:

- cp310-cp310
- cp311-cp311
- cp312-cp312
- cp313-cp313


Reference: https://github.com/pypa/manylinux
