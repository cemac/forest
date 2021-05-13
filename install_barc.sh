#!/bin/bash -
#title          :installbarc.sh
#description    :This script installs forest and barc
#author         :CEMAC - Helen
#date           :20210326
#version        :1.0
#usage          :./installbarc.sh
#notes          :
#bash_version   :4.2.46(2)-release
#============================================================================
echo "downloading submodules"
# install submodules
git submodule init
git submodule update --init --recursive
# create blank database file
cp -p forest/barc/barc-save_template.sdb forest/barc/barc-save.sdb 
# create and activate virtual environment
conda create --name forest-barc
whichconda=$(which conda |  awk -F/ '{print $(NF-2)}')
. $HOME/$whichconda/etc/profile.d/conda.sh
conda activate forest-barc
conda install -c conda-forge --file requirements.txt --file requirements-dev.txt -y
python setup.py develop
echo "set up complete"
