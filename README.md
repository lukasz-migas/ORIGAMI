# ORIGAMI - Software for analysis of MS and IM-MS data

## Notes

A number of features are still broken in ORIGAMI. I am slowly working through them to make them available again,
however, you are free to try out new version of ORIGAMI already. There have been numerous improvements
and changes made throughout the software.

Still broken:

- Cannot apply ORIGAMI-MS parameters to heatmap objects (difficulty: EASY)
- Cannot export data in an interactive format (difficulty: HARD)
- Cannot run UniDec deconvolution (difficulty: HARD)
- Cannot 


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

