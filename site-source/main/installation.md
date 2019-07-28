# Installation

## Packaged installation

### Download

You can download the latest version of **ORIGAMI-ANALYSE** from [GitHub](https://github.com/lukasz-migas/ORIGAMI/releases).

### Getting Started

Actually, there is no actual installation! Simply copy the zipped folder onto your machine, unpack it and that's it! To start ORIGAMI-ANALYSE, double-click on the **ORIGAMI.exe** file.

### Requirements

Requirements: Windows 7/8/10
HDD space: ~1 Gb
Optional: Waters Driftscope (v2.7+)

### Troubleshooting

If, when you double-click on ORIGAMI.exe and a command window pops-up for a fraction of a second, you might want to try running it from the command line. The easiest way to do it is to follow these steps.

1. Go to the unzipped ORIGAMI directory
2. In the Windows Explorer, click on the address bar and type **cmd**. This will bring up a Windows command window where you can log issues associated with ORIGAMI.exe
3. In the command window type in **ORIGAMI.exe**
4. If its working, a new window should appear and if its not, you will see some error messages

5. PyInstallerImportError

A number of Windows 10 users have reported issues opening ORIGAMI.exe. It typically comes with this message:

    PyInstallerImportError: Failed to load dynlib/dll 'C:\\Users\\USER\\ORIGAM~1.4\\ORIGAM~1.4\\MassLynxRaw.dll'. Most probably this dynlib/dll was not found when the application was frozen.
    [3428] Failed to execute script ORIGAMI

This problem is caused by a missing C++ library and can be easily solved by installing [Visual C++ 2010 Redistributable Package](https://www.microsoft.com/en-us/download/confirmation.aspx?id=14632)

## From source

### Download

You can clone/copy the [GitHub](https://github.com/lukasz-migas/ORIGAMI) directory and only looking at the contents of ORIGAMI_ANALYSE/origami

### Requirements

Windows 7/8/10
Python 2.7
WxPython==3.0.2
[List of dependancies](https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/origami/origami_requirements.txt)
Optional: Waters Driftscope (v2.7+)

### Recomendations

You are best of using conda or python environments to keep your Python installation nice and tidy. In order to create a conda environment, open a command window and type-in

```python
conda create -n origami
```

To activate this environment, type-in

```python
activate origami
```

To run ORIGAMI from source, type-in

```python
python origami.py
```

If you have installed all dependancies, you should be good! :)
