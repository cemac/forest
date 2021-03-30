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
git submodule init
git submodule update --init --recursive
cp -p forest/barc/barc-save_template.sdb forest/barc/barc-save.sdb 
conda create --name forest-barc
conda install -c conda-forge --file requirements.txt --file requirements-dev.txt -y
python setup.py develop
