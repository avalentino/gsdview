#!/usr/bin/env python

# -*- coding: UTF8 -*-

### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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
import fnmatch

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

packages = ['gsdview', 'gsdview.exectools', 'gsdview.plugins',
            'gsdview.plugins.gdal_band_overview',
            'gsdview.plugins.gdal_dataset_browser',
            'gsdview.plugins.gdal_metadata_viewer',
            'gsdview.plugins.position_tracker',
            'gsdview.plugins.worldmap_panel',
            'gsdview.plugins.zoom_tools',
]

def datatree(root, include=None, exclude=None):
    datafiles = []
    for path, dirs, files in os.walk(root):
        datafiles.extend([os.path.join(path, file_) for file_ in files])
    if include:
        files = fnmatch.filter(files, include)
    if exclude:
        excludefiles = fnmatch.filter(datafiles, exclude)
        datafiles = list(set(datafiles).difference(excludefiles))
    return datafiles

datafiles = [
    (os.path.join('share', 'doc', PKGNAME), ['README.txt']),
    (os.path.join('share', 'doc', PKGNAME, 'html'),
                    datatree(os.path.join('doc', 'build', 'html'))),
    (os.path.join('share', 'doc', PKGNAME),
                    [os.path.join('doc', 'build', 'latex', 'GSDView.pdf')]),
    # @TODO: unix only
    ('share/applications', ['gsdview.desktop']),
    ('share/pixmaps', ['images/GSDView.png']),
]

setup(name             = PKGNAME,
      version          = info.version,
      description      = info.short_description,
      long_description = info.description,
      author           = info.author,
      author_email     = info.author_email,
      maintainer       = info.author,
      maintainer_email = info.author_email,
      url              = info.website,
      #download_url = "http://www.pytables.org/download/stable/pytables-%s.tar.gz" % VERSION,
      packages         = packages,
      package_data     = {'gsdview': ['ui/*.ui'],
                          'gsdview.plugins.gdal_dataset_browser': ['*.ui'],
                         },
      scripts          = ['gsdviewer'],
      classifiers      = filter(None, classifiers.split('\n')),
      license          = info.license_type,
      platforms        = ['any'],
      data_files       = datafiles,
      #cmdclass         = cmdclass,
      **setuptools_kwargs
     )
