#!/usr/bin/env python

# -*- coding: UTF8 -*-

### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__revision__ = '$Revision$'

import os
import glob

from gsdview import info

# Using ``setuptools`` enables lots of goodies, such as building eggs.
#~ try:
    #~ from setuptools import setup, find_packages
    #~ has_setuptools = True
#~ except ImportError:
    #~ from distutils.core import setup
    #~ has_setuptools = False

from distutils.core import setup
has_setuptools = False

PKGNAME = info.name.lower()

classifiers = '''\
Development Status :: 3 - Alpha
Environment :: Win32 (MS Windows)
Environment :: X11 Applications :: Qt
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: End Users/Desktop
Intended Audience :: Science/Research
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Education
Topic :: Scientific/Engineering :: Astronomy
Topic :: Scientific/Engineering :: GIS
Topic :: Scientific/Engineering :: Visualization
'''

if has_setuptools:
    setuptools_kwargs = dict(
        #install_requires = ['GDAL >= 1.4.4',
        #                    'numpy >= 1.0.4',
        #                    'scipy >= 0.6.0',
        #                    #'PyQt4 >= 4.3.3',
        #                   ],
        #extras_require = {},
        keywords = 'gsdview gdal',
        zip_safe = True,
        #entry_points = {
        #    #'console_scripts': ['gsdview = gsdview.gsdview.main'],
        #    'gui_scripts': ['gsdview = gsdview.gsdview.main'],
        #    #'setuptools.installation': ['eggsecutable = gsdview.gsdview.main',]
        #}
    )
else:
    setuptools_kwargs = {}

packages = ['gsdview', 'gsdview.exectools', 'gsdview.plugins']

plugindir = os.path.join('gsdview', 'plugins')
for dir_ in os.listdir(plugindir):
    if os.path.isdir(os.path.join(plugindir,dir_)) and not dir_.startswith('.'):
        packages.append('gsdview.plugins.%s' % dir_)

datafiles = [
    (os.path.join('share', 'doc', PKGNAME), ['README.txt']),
]

setup(name             = PKGNAME,
      version          = info.version,
      description      = info.short_description,
      long_description = info.description,
      author           = ', '.join(info.author),
      author_email     = ', '.join(info.author_email),
      maintainer       = ', '.join(info.author),
      maintainer_email = ', '.join(info.author_email),
      url              = info.website,
      #download_url = "http://www.pytables.org/download/stable/pytables-%s.tar.gz" % VERSION,
      packages         = packages,
      scripts          = ['gsdviewer'],
      classifiers      = filter(None, classifiers.split('\n')),
      license          = info.license_type,
      platforms        = ['any'],
      #data_files       = datafiles,
      #cmdclass         = cmdclass,
      **setuptools_kwargs
     )
