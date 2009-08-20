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


__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import platform
from glob import glob

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
Development Status :: 4 - Beta
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
        #install_requires = ['GDAL >= 1.5.2',
        #                    'numpy >= 1.2.1',
        #                    'PyQt >= 4.5',
        #                   ],
        #extras_require = {},
        keywords = 'gsdview gdal',
        zip_safe = True,
        #entry_points = {
        #    'gui_scripts': ['gsdview = gsdview.gsdview.main'],
        #    #'setuptools.installation': ['eggsecutable = gsdview.gsdview.main',]
        #}
    )
else:
    setuptools_kwargs = {}

packages = ['gsdview', 
            'gsdview.exectools', 
            'gsdview.gdalbackend',
            'gsdview.plugins',
            'gsdview.plugins.overview',
            'gsdview.plugins.metadata',
            'gsdview.plugins.positiontracker',
            'gsdview.plugins.worldmap',
            'gsdview.plugins.zoom',
]

datafiles = [
    (os.path.join('share', 'doc', PKGNAME), ['README.txt']),
    (os.path.join('share', 'doc', PKGNAME, 'html'),
        [name for name in glob(os.path.join('doc', 'html', '*'))
                                                if not os.path.isdir(name)]),
    (os.path.join('share', 'doc', PKGNAME, 'html', '_sources'),
        [name for name in glob(os.path.join('doc', 'html', '_sources', '*'))
                                                if not os.path.isdir(name)]),
    (os.path.join('share', 'doc', PKGNAME, 'html', '_static'),
        [name for name in glob(os.path.join('doc', 'html', '_static', '*'))
                                                if not os.path.isdir(name)]),

    #(os.path.join('share', 'doc', PKGNAME),
    #                [os.path.join('doc', 'GSDView.pdf')]),
]

if os.name == 'posix':
    if platform.system() == 'FreeBSD':
        mandir = 'man'
    else:
        mandir = os.path.join('share', 'man')
    datafiles.append((os.path.join(mandir, 'man1'), ['debian/gsdview.1']))
    datafiles.append((os.path.join(mandir, 'man1'), ['debian/gsdviewer.1']))
    datafiles.append((os.path.join('share', 'applications'),
                        ['gsdview.desktop']))
    datafiles.append((os.path.join('share', 'pixmaps'),
                        [os.path.join('images', 'GSDView.png')]))

if not platform.dist()[0] in ('Dabian', 'Ubuntu'):
    datafiles.append((os.path.join('share', 'doc', PKGNAME), ['LICENSE.txt']))

setup(name             = PKGNAME,
      version          = info.version,
      description      = info.short_description,
      long_description = info.description,
      author           = info.author,
      author_email     = info.author_email,
      maintainer       = info.author,
      maintainer_email = info.author_email,
      url              = info.website,
      download_url     = info.download_url,
      packages         = packages,
      package_data     = {'gsdview': ['ui/*.ui'],
                          'gsdview.gdalbackend': ['ui/*.ui'],
                         },
      scripts          = ['gsdviewer'],
      classifiers      = filter(None, classifiers.split('\n')),
      license          = info.license_type,
      platforms        = ['any'],
      data_files       = datafiles,
      #cmdclass         = cmdclass,
      **setuptools_kwargs
     )
