import sys
import zipfile
from distutils.core import setup
import py2exe
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import pylab
import numpy
import path
import os
import sys
import bokeh.core
import bokeh.events
import scipy, scipy.stats
from shutil import copy

sys.setrecursionlimit(5000)
version = '1.0.4'

# Compile program using:
# python compileScript.py py2exe

# add any numpy directory containing a dll file to sys.path
def numpy_dll_paths_fix():
    paths = set()
    np_path = numpy.__path__[0]
    for dirpath, _, filenames in os.walk(np_path):
        for item in filenames:
            if item.endswith('.dll'):
                paths.add(dirpath)

    sys.path.append(*list(paths))

numpy_dll_paths_fix()

current_dir = os.path.dirname(os.path.realpath(__file__))
dist_dir = os.path.join(current_dir, "ORIGAMI_ANALYSE_v1.0.4")


# py2exe options
py2exe_options = dict(
    compressed = True,
    optimize = 1,
    excludes = ["Tkconstants","Tkinter","tcl","Qt","PyQt4", 
                "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list","h5py","babel",
                "pdb", '_ssl','Qt5','nbconvert','IPython'],
    includes = ["matplotlib.backends.backend_qt5agg", "PyQt5", 
                "scipy.sparse.csgraph._validation", "scipy.linalg.cython_blas",
                "scipy.linalg.*","scipy.integrate", "scipy.special", "scipy",
                "scipy.special._ufuncs_cxx", "scipy.special.*", 
                "scipy.special._ufuncs","scipy.stats", 
                "email.mime.*", "jinja2",
                "bokeh.core", "bokeh.events"],
    packages = ["wx.lib.pubsub", "pkg_resources"],
    dll_excludes=['msvcr71.dll','hdf5.dll'],
    dist_dir = dist_dir,
    )



# main setup
setup(name = "ORIGAMI",
      version = '1.0.4',
      description = "ORIGAMI - A Software Suite for Activated Ion Mobility Mass Spectrometry ",
      author = "Lukasz G. Migas",
      url = 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
      windows = [{ "script": "ORIGAMI.py",
                   "icon_resources": [(1, "icon_old.ico")]}],
      console = [{ "script": "ORIGAMI.py"}],
	  data_files=matplotlib.get_py2exe_datafiles(),
      options = dict(py2exe = py2exe_options),
      )
    
    

	# Copy additional files
filelist = [
'icon.ico', 
'MassLynxRaw.dll', 
'UserGuide_ANALYSE.pdf', 
'calibrantDB.csv', 
'calibrantDB.xlsx'
]
savePath = path.path(''.join([dist_dir,'\\']))
for file in filelist:
	print(file)
	copy(file, savePath)
	
# Add bokeh/core/_templates files to the library.zip file
bokeh_path = sys.modules['bokeh.core'].__path__[0]
zipfile_path = os.path.join(dist_dir, "library.zip")
z = zipfile.ZipFile(zipfile_path, 'a')
for dirpath,dirs,files in os.walk(os.path.join(bokeh_path, '_templates')):
  for f in files:
      fn = os.path.join(dirpath, f)
      z.write(fn, os.path.join(dirpath[dirpath.index('bokeh'):], f))
z.close()
    

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	