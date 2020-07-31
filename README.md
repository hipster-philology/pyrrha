Pyrrha
======

[![Coverage Status](https://coveralls.io/repos/github/hipster-philology/ppyrrha/badge.svg?branch=master)](https://coveralls.io/github/hipster-philology/pyrrha?branch=master)
[![Build Status](https://travis-ci.org/hipster-philology/pyrrha.svg?branch=master)](https://travis-ci.org/hipster-philology/pyrrha)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2325427.svg)](https://doi.org/10.5281/zenodo.2325427)


Pyrrha is a simple Python Flask WebApp to fasten the post-correction
of lemmatized and morpho-syntactic tagged corpora.

# How to cite

This web application and its maintenance is done by Julien Pilla (@MrGecko) and Thibault Clérice (@ponteineptique). To learn **how to cite** this repository, go check [our releases](https://github.com/hipster-philology/pyrrha/releases).

```latex
@software{thibault_clerice_2019_3524771,
  author       = {Clérice, Thibault and Pilla, Julien and Camps, Jean-Baptiste and Jolivet, Vincent and Pinche, Ariane},
  title        = {Pyrrha, A language independant post correction app for POS and lemmatization},
  month        = nov,
  year         = 2019,
  publisher    = {Zenodo},
  version      = {Any Version},
  doi          = {10.5281/zenodo.2325427},
  url          = {https://doi.org/10.5281/zenodo.2325427}
}
```

# Credits

This software is built as an addition to the tagger Pie by Enrique Manjavacas (@emanjavacas) and Mike Kestemont (@mikekestemont) [![DOI](https://zenodo.org/badge/131014015.svg)](https://zenodo.org/badge/latestdoi/131014015)

## Demo
![Pandora Post-Correction Editor](./demo.gif)

## Install

Start by cloning the repository, and moving inside the created folder

```bash
git clone https://github.com/hipster-philology/pyrrha.git
cd pyrrha/
```

Create a virtual environment, source it and run

```bash
pip install -r requirements.txt
python manage.py db-create
```

## Run

```bash
python manage.py run
```

## How to contribute

- See [Contribute.md](contribute.md)

## Source

This app is wished to be simple and local at the moment (No User system). But to keep in the abilities to extend and use
other systems, we based some of our decisions on https://github.com/hack4impact/flask-base/ and the general structure is following theirs.
