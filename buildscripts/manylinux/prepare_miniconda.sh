#!/bin/bash
set -e
cd /root
curl -L -o mini3.sh $1
bash mini3.sh -b -f -p /root/miniconda3
echo "Miniconda installed"
source /root/miniconda3/bin/activate base
echo "Env activated"
cd -
