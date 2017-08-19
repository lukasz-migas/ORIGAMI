import sys
import zipfile
from distutils.core import setup
import py2exe
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy
import os
import sys
# import bokeh.core
# 
# __import__('pkg_resources').declare_namespace(__name__)
# import modulefinder
# for p in __path__:
#    modulefinder.AddPackagePath(__name__, p)

sys.setrecursionlimit(5000)

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
dist_dir = os.path.join(current_dir, "ORIGAMI_MS_v1.0.0-alpha")

# py2exe options
py2exe_options = dict(
#     bundle_files = 1,
    compressed = True,
    optimize = 0,
    bundle_files = 3,
    excludes = ["Tkconstants","Tkinter","tcl","Qt","PyQt5.*","PyQt4", 
                "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list",
                "scipy.*", "pandas.*","pdb","doctest"],
    includes = ["matplotlib.backends.backend_qt5agg", 
                "email.mime.*", "jinja2", "bokeh.core"],
    packages = ["wx.lib.pubsub", "pkg_resources"],
    dll_excludes = ["Qt5Gui","Qt5Widgets","Qt5Svg","Qt5Gui"],
    dist_dir = dist_dir,
    )




# main setup
setup(name = "ORIGAMI-MS",
      version = 'v1.0.0-alpha',
      description = "ORIGAMI - A Software Suite for Activated Ion Mobility Mass Spectrometry ",
      author = "Lukasz G. Migas",
      url = 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
      windows = [{ "script": "ORIGAMIMS.py",
                   "icon_resources": [(1, "icon.ico")]}],
      console = [{ "script": "ORIGAMIMS.py"}],
      data_files=matplotlib.get_py2exe_datafiles(),
      options = dict(py2exe = py2exe_options),
      )
    
    
# # Add bokeh/core/_templates files to the library.zip file
# bokeh_path = sys.modules['bokeh.core'].__path__[0]
# zipfile_path = os.path.join(dist_dir, "library.zip")
# z = zipfile.ZipFile(zipfile_path, 'a')
# for dirpath,dirs,files in os.walk(os.path.join(bokeh_path, '_templates')):
#   for f in files:
#       fn = os.path.join(dirpath, f)
#       z.write(fn, os.path.join(dirpath[dirpath.index('bokeh'):], f))
# z.close()
    