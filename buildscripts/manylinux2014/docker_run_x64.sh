export ARCH="x86_64"
export MINICONDA_FILE="https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
