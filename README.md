# ORIGAMI - Software for analysis of MS and IM-MS data

![Tests](https://github.com/lukasz-migas/ORIGAMI/workflows/Tests/badge.svg)
[![codecov](https://codecov.io/gh/lukasz-migas/ORIGAMI/branch/dev-py3/graph/badge.svg)](https://codecov.io/gh/lukasz-migas/ORIGAMI)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/ee92e286b9c74ac0aa583df9a3b2daac)](https://www.codacy.com/manual/lukasz-migas/ORIGAMI?utm_source=github.com&utm_medium=referral&utm_content=lukasz-migas/ORIGAMI&utm_campaign=Badge_Grade)
[![CodeFactor](https://www.codefactor.io/repository/github/lukasz-migas/origami/badge)](https://www.codefactor.io/repository/github/lukasz-migas/origami)

## Notes

A number of features are still broken in ORIGAMI. I am slowly working through them to make them available again,
however, you are free to try out new version of ORIGAMI already. There have been numerous improvements
and changes made throughout the software.

Still broken:

-   Cannot apply ORIGAMI-MS parameters to heatmap objects (difficulty: EASY)
-   Cannot export data in an interactive format (difficulty: HARD)
-   Cannot run UniDec deconvolution (difficulty: HARD)
-   Cannot compare data using the `Comparison` visualizer (difficulty: HARD)

Features to be implemented:

-   Add CCS calculation module
-   Add linear Drift-Tube analysis module
-   Add fast 3D visualisation
-   Add MS/MS visualisation
-   Add UVPD analysis module

## Installation

In order to install the development version of ORIGAMI, I recommend using a designated virtual environment (e.g. conda, virtualenv, etc)

If you don't have miniconda, install it  first

[Install Miniconda](https://docs.conda.io/en/latest/miniconda.html)

Using conda

```python
conda create -n origami python=3.7
activate origami
```

**Do all of the following commands from within the main ORIGAMI directory**

Install all requirements (Windows)

```python
pip install -r requirements/requirements-std.txt
pip install -r requirements/requirements-wx.txt
pip install -r requirements/requirements-win32.txt 
```

Install ORIGAMI (just installation)

```python
python setup.py install
```

Or if you would like to make changes to the source code, use the following:

```python
pip install -r requirements/requirements-dev.txt
python setup.py develop
```

Start ORIGAMI

```python
origami.exe
```

## Check your installation

Activate your environment like above and install development requirements. This will install a number of packages that
are used to test ORIGAMI codebase. The test suite is still under development and a lot of the codebase is not covered,
however, a portion of it is.

```python
# Do this from within the main ORIGAMI directory and not `origami` (small letters)
pip install -r requirements/requirements-dev.txt
```

This command will run ALL the tests (GUI + logic)

```python
pytest .
```

If you only want to run the GUI tests, invoke

```python
pytest . -m guitest
```

Or if you only want to run the logic tests, invoke

```python
pytest . -m "not guitest"
```
