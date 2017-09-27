Pandora TAB Post-correction App
===============================================

![Pandora Post-Correction Editor](./readme.png)

# Install

Create a virtual environment, source it and run

```bash
pip install -r requirements.txt
python manager.py create_db
```

# Run

```bash
pip install -r requirements.txt
python manager.py run
```

# Source

This app is wished to be simple and local at the moment (No User system). But to keep in the abilities to extend and use
other systems, we based some of our decisions on https://github.com/hack4impact/flask-base/ and the general structure is following theirs.