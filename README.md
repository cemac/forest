<h1 align="center">
  <a href="https://barc-docs.readthedocs.io/en/latest/" style="display: block; margin: 0 auto;">
   <img src="https://github.com/cemac/forest-barc/blob/master/forest/barc/icons/barclogo.png"
        style="max-width: 40%;" alt="BARC logo"></a>
</h1>

<span><strong>BARC - </strong> 
   Bokeh Annotation and Reporting Component
  </span>

![GitHub](https://img.shields.io/github/license/cemac/forest-barc.svg) [![GitHub top language](https://img.shields.io/github/languages/top/cemac/forest-barc.svg)](https://github.com/cemac/forest-barc) [![GitHub issues](https://img.shields.io/github/issues/cemac/forest-barc.svg)](https://github.com/cemac/forest-barc/issues) [![GitHub last commit](https://img.shields.io/github/last-commit/cemac/forest-barc.svg)](https://github.com/cemac/forest-barc/commits/master) [![GitHub All Releases](https://img.shields.io/github/downloads/cemac/forest-barc/total.svg)](https://github.com/cemac/forest-barc/releases)
  [![HitCount](http://hits.dwyl.com/{cemac}/{forest-barc}.svg)](http://hits.dwyl.com/{cemac}/{forest-barc}) [![DOI](https://zenodo.org/badge/248009615.svg)](https://zenodo.org/badge/latestdoi/248009615)



<hr>

## About

The Bokeh Annotation and Reporting Component (BARC) is a component integrated into the FOREST visualisation tool. It allows the users to annotate and markup data within FOREST.

## Documentation

Please read the [docs](https://barc-docs.readthedocs.io/en/latest/) 
These are a work in progress but include user documentation, developer guides and api references. Hopfully these will become an invaluable resource for getting up and running with BARC.

## Installation 

The reccomendend method for installation is using git and anaconda.
1. `git clone` this repo
2. run `./install_barc.sh` 

This will install the font submodule, create a blank database file, create a conda environment and install the requirements.

then an example run command would be:

`forest --dev --config-file testbarc.yml --show; pkill -9 python`

## Get in touch
BARC has been developed by a small team of Developers, but we are keen to hear from you with your suggestions for improvements. If you have suggestions for improvements, bugs that need reporting feel free to open/comment on [issues](https://github.com/cemac/forest-barc/issues).

## License

BARC is licensed under the BSD 3-clause license

© Crown copyright 2020, NCAS. 
