# -*- mode: python -*-
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE, TOC
from PyInstaller.utils.hooks import get_package_paths, remove_prefix, PY_IGNORE_EXTENSIONS

import sys
import zipfile
from distutils.core import setup
from distutils.dir_util import copy_tree
import py2exe
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import requests.certs
import certifi
import pylab
import numpy
import path
import os
import sys
import bokeh.core
import bokeh.events
import bokeh.server
import bokeh
import scipy, scipy.stats
from shutil import copy
import wx
import time
import json
import wx.lib.pubsub as pub
import pymzml
print("wxPython version: {}".format(wx.__version__))


tstart_build = time.clock()

block_cipher = None

# run command
# pyinstaller ORIGAMI.spec -y --clean

# Set version number
version = "1.2.1.6"

current_dir = os.getcwd()
origami_dir_name = "ORIGAMI_v{}".format(version)
dist_dir = os.path.join(current_dir, "dist\\{}".format(origami_dir_name))
print("Creating executable in {}".format(dist_dir))

def collect_pkg_data(package, include_py_files=False, subdir=None):
    # Accept only strings as packages.
    if type(package) is not str:
        raise ValueError

    pkg_base, pkg_dir = get_package_paths(package)
    if subdir:
        pkg_dir = os.path.join(pkg_dir, subdir)
    # Walk through all file in the given package, looking for data files.
    data_toc = TOC()
    for dir_path, dir_names, files in os.walk(pkg_dir):
        for f in files:
            extension = os.path.splitext(f)[1]
            if include_py_files or (extension not in PY_IGNORE_EXTENSIONS):
                source_file = os.path.join(dir_path, f)
                dest_folder = remove_prefix(dir_path, os.path.dirname(pkg_base) + os.sep)
                dest_file = os.path.join(dest_folder, f)
                data_toc.append((dest_file, source_file, 'DATA'))

    return data_toc

def dir_files(path, rel):
    ret = []
    for p, d, f in os.walk(path):
        relpath = p.replace(path, '')[1:]
        for fname in f:
            ret.append((os.path.join(rel, relpath, fname),
                        os.path.join(p, fname), 'DATA'))
    return ret

pkg_data = collect_pkg_data('jinja2')

a = Analysis(['ORIGAMI.py'],
             pathex=[os.getcwd()],
             binaries=[],
             datas=[#(r'C:\\Program Files\\Anaconda\\Lib\\site-packages\\bokeh\\core\\_templates', '_templates'), 
                    #(r'C:\\Program Files\\Anaconda\\site-packages\\bokeh\\server', 'server')],
                    ],
             hiddenimports=[
                 "scipy.sparse.csgraph._validation", 
                 "scipy.linalg.cython_blas", "scipy.linalg.*","scipy.integrate", 
                 "scipy.special", "scipy", "scipy.special._ufuncs_cxx", 
                 "scipy.special.*", "scipy.special._ufuncs", "scipy.stats", 
                 'scipy._lib.messagestream',
                 "pkg_resources", 'wx.lib.pubsub', 
                 'wx.lib',
                 'wx.lib.pubsub', 'wx.lib.pubsub.core.publisherbase', 
                 'wx.lib.pubsub.core.kwargs', 'wx.lib.pubsub.core.kwargs.publisher',
                 'wx.lib.pubsub.core.kwargs.listenerimpl', 'wx.lib.pubsub.core.kwargs.publishermixin',
                 'wx.lib.pubsub.core.listenerbase', 'wx.lib.pubsub.core', 
                 'wx.lib.pubsub.core.kwargs.topicargspecimpl',
                 'wx.lib.pubsub.core.kwargs.topicmgrimpl',
                 'six', "bokeh", "nodejs", "adjustText", "cmocean", "multiplierz",
                 'pymzml.run', 'pymzml.obo',
                 'pandas._libs.tslibs.np_datetime','pandas._libs.tslibs.nattype','pandas._libs.skiplist'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['IPython', 'Cython', 'statsmodels', 'pyQT5',
                       'GdkPixbuf', 'pyQT4', 'pygobject', 'pygtk', 'pyside'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas.extend(dir_files(os.path.join(os.path.dirname(pymzml.__file__), 'obo'), 'obo'))
# a.datas.extend(dir_files("multiplierz", 'multiplierz'))


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='ORIGAMI',
          debug=False,
          strip=False,
          upx=True,
          console=True, 
          icon='icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               pkg_data,
               strip=False,
               upx=True,
               name=dist_dir)

# Give information about build time
tend_build = time.clock()
print("Build ORIGAMI in {} seconds\n".format(tend_build-tstart_build))

# Copy additional files
filelist = ['icon.ico', 'MassLynxRaw.dll', 'calibrantDB.csv',
            'calibrantDB.xlsx', 'cacert.pem', 'node-v10.14.1-x64.msi']

tstart_copy = time.clock()
savePath = path.path(''.join([dist_dir,'\\']))
for file in filelist:
  try:
      copy(file, savePath)
      print("Copied file: {}".format(file))
  except:
    print("Skipped file: {}".format(file))
  
# Copy additional folders
dirlist = ['licences', 'unidec_bin', 'images', 'example_files', 'docs'
           # r'C:\\Program Files\\Anaconda\\Lib\\site-packages\\bokeh\\core\\_templates',
           # r'C:\\Program Files\\Anaconda\\Lib\\site-packages\\bokeh\\server'
           ]
           
for directory in dirlist:
  try:
    tstart_copying = time.clock()
    saveDir = path.path(''.join([dist_dir,'\\', directory]))
    copy_tree(directory, saveDir)
    print("Copied directory: {}. It took {:.4f} seconds.".format(directory, time.clock()-tstart_copying))
  except:
    print('Skipped directory: {}'.format(directory))
    pass

print("Copied files in {} seconds.\n".format(time.clock()-tstart_copy))
print("ORIGAMI was compiled in {:.4f} seconds.\n".format(time.clock()-tstart_build))


