export MANYLINUX_IMAGE="manylinux2014_x86_64"
export MINICONDA_FILE="https://repo.anaconda.com/miniconda/Miniconda3-py311_24.9.2-0-Linux-x86_64.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
