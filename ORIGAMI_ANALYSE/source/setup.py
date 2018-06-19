# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# Generate icon: convert logo.png -define icon:auto-resize=128,64,48,32,16 logo.ico


import sys
import zipfile
from distutils.core import setup
from distutils.dir_util import copy_tree
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
import wx
#import pyface
#import tvtk
#import mayavi
#import vtk
# 
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'wx'

sys.setrecursionlimit(5000)
version = '1.1.1'

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
dist_dir = os.path.join(current_dir, "ORIGAMI_ANALYSE_v1.1.1")

# def copyPackage (pkg, name, dist) :
#     p = os.path.join (dist, name)
#     copy_tree (pkg.__path__[0], p)


#copyPackage (tvtk, "tvtk", dist_dir)
#copyPackage (mayavi, "mayavi", dist_dir)
#copyPackage (pyface, "pyface", dist_dir)
#copyPackage (vtk, "vtk", dist_dir)


# py2exe options
py2exe_options = dict(
    compressed = True,
    optimize = 1,
    excludes = ["tcl","Qt","PyQt4", 
                "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list","h5py","babel",
                "pdb", '_ssl','Qt5','nbconvert','IPython',
				],
    includes = ["matplotlib.backends.backend_qt5agg", "PyQt5", 
   				"urllib2",
                "scipy.sparse.csgraph._validation", 
				"scipy.linalg.cython_blas",
                "scipy.linalg.*","scipy.integrate", 
				"scipy.special", 
				"scipy",
                "scipy.special._ufuncs_cxx", 
				"scipy.special.*", 
                "scipy.special._ufuncs",
				"scipy.stats", 
                "email.mime.*", 
                'scipy._lib.messagestream',
				"jinja2",
                "bokeh.core", "bokeh.events",
                "matplotlib.backends.backend_tkagg",
                "Tkinter", "Tkconstants",
                #"traits", "traits.*"
                ],
    packages = ["wx.lib.pubsub", "pkg_resources"],#, "traits", "mayavi", "tvtk", "vtk"],
    dll_excludes=['msvcr71.dll','hdf5.dll'],
    dist_dir = dist_dir,
    bundle_files = 3,
    xref = False
    )



# main setup
setup(name = "ORIGAMI",
      version = '1.1.1',
      description = "ORIGAMI - A Software Suite for Activated Ion Mobility Mass Spectrometry ",
      author = "Lukasz G. Migas",
      contact = "lukasz.migas@manchester.ac.uk",
      url = 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
      windows = [{ "script": "ORIGAMI.py",
                   "icon_resources": [(1, "icon.ico")]}],
      console = [{ "script": "ORIGAMI.py"}],
	  data_files=matplotlib.get_py2exe_datafiles(),
      zipfile='lib/library.zip',
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
	
# Copy additional folders
dirlist = [ 'licences', 'unidec_bin', 'images'] #, 'mpl-data']
for directory in dirlist:
	try:
		saveDir = path.path(''.join([dist_dir,'\\', directory]))
		copy_tree(directory, saveDir)
	except:
		print('skip')
		pass

# Add bokeh/core/_templates files to the library.zip file
bokeh_path = sys.modules['bokeh.core'].__path__[0]
zipfile_path = os.path.join(dist_dir, "lib\library.zip")
z = zipfile.ZipFile(zipfile_path, 'a')
for dirpath,dirs,files in os.walk(os.path.join(bokeh_path, '_templates')):
  for f in files:
      fn = os.path.join(dirpath, f)
      z.write(fn, os.path.join(dirpath[dirpath.index('bokeh'):], f))
z.close()
    

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	