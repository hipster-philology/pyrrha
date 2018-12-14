Pyrrha
======

[![Coverage Status](https://coveralls.io/repos/github/hipster-philology/pandora-postcorrect-app/badge.svg?branch=master)](https://coveralls.io/github/hipster-philology/pandora-postcorrect-app?branch=master)
[![Build Status](https://travis-ci.org/hipster-philology/pandora-postcorrect-app.svg?branch=master)](https://travis-ci.org/hipster-philology/pandora-postcorrect-app)

Pyrrha is a simple Python Flask WebApp to fasten the post-correction
of lemmatized and morpho-syntactic tagged corpora.

![Pandora Post-Correction Editor](./readme.png)

![Pandora Post-Correction Editor](./history.png)

![Pandora Post-Correction Editor](./batch_changes.png)

## Install

Start by cloning the repository, and moving inside the created folder

```bash
git clone https://github.com/hipster-philology/pandora-postcorrect-app.git
cd pandora-postcorrect-app/
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
