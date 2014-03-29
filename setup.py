#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <a_valentino@users.sf.net>

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

import os
import sys
import platform
import traceback

from gsdview import info
from exectools import __version__ as exectools_version
from gsdtools import __version__ as gsdtools_version


PKGNAME = info.name.lower()

cmdclass = {}
kwargs = {}


# Using ``setuptools`` enables lots of goodies, such as building eggs.
from distutils import log
from distutils.command.build import build as Build
try:
    has_setuptools = True

    from setuptools import setup, find_packages
    from setuptools.command.install_lib import install_lib

    if sys.version_info[0] >= 3:
        kwargs['use_2to3'] = True
        kwargs['use_2to3_fixers'] = []
        kwargs['use_2to3_exclude_fixers'] = ['lib2to3.fixes.fix_standarderror']

except ImportError:
    has_setuptools = False

    from distutils.core import setup
    from distutils.command.install_lib import install_lib

    try:
        from distutils.command.build_py import build_py_2to3
        from distutils.command.build_scripts import build_scripts_2to3
    except ImportError:
        pass
    else:
        from lib2to3.refactor import get_fixers_from_package

        fixers = get_fixers_from_package('lib2to3.fixes')
        fixers.remove('lib2to3.fixes.fix_standarderror')

        cmdclass['build_py'] = build_py_2to3
        cmdclass['build_scripts'] = build_scripts_2to3


try:
    from sphinx.setup_command import BuildDoc

    class BuildMan(BuildDoc):
        def initialize_options(self):
            BuildDoc.initialize_options(self)
            self.builder = 'man'

    cmdclass['build_man'] = BuildMan
except ImportError:
    pass


class ExtendedBuild(Build):
    def run(self):
        Build.run(self)
        try:
            self.run_command('build_sphinx')
            if 'build_man' in cmdclass:
                self.run_command('build_man')
        except:
            log.warn("Couldn't build documentation:\n%s" %
                     traceback.format_exception(*sys.exc_info()))

# @NOTE: temporary disabled because could break debian packaging.
#        The man page and docs are included in the source package generated
#        via makefile.
#cmdclass['build'] = ExtendedBuild

if has_setuptools:
    from setuptools.command.bdist_egg import bdist_egg

    class ExtendedBdistEgg(bdist_egg):
        def run(self):
            try:
                self.run_command('build_sphinx')
                if 'build_man' in cmdclass:
                    self.run_command('build_man')
            except:
                log.warn("Couldn't build documentation:\n%s" %
                         traceback.format_exception(*sys.exc_info()))
            bdist_egg.run(self)

    # @NOTE: temporary disabled because could break debian packaging.
    #        The man page and docs are included in the source package
    #        generated via makefile.
    #cmdclass['bdist_egg'] = ExtendedBdistEgg


# Fix the install_lib command in order to generate an updated appsite.py file
class InstallLib(install_lib):

    stdinstall_schema = '''\
__all__ = ['DATADIR', 'DOCSDIR', 'LICENSEFILE', 'SYSPLUGINSDIR']

import os
PKGNAME = 'gsdview'

DATADIR = os.path.join('%(DATADIR)s', 'share', PKGNAME)
DOCSDIR = os.path.join('%(DATADIR)s', 'share', 'doc', PKGNAME)
LIBDIR = os.path.dirname(os.path.abspath(__file__))
SYSPLUGINSDIR = os.path.join(LIBDIR, 'plugins')

LICENSEFILE = os.path.join(DOCSDIR, 'LICENSE.txt')
USERCONFIGDIR = os.path.expanduser(os.path.join('~', '.gsdview'))

if not os.path.exists(DOCSDIR):
    try:
        import pkg_resources

        req = pkg_resources.Requirement.parse(PKGNAME)
        SHAREDIR = pkg_resources.resource_filename(req, 'share')
        DATADIR = os.path.join(SHAREDIR, PKGNAME)
        DOCSDIR = os.path.join(SHAREDIR, 'doc', PKGNAME)
        LICENSEFILE = os.path.join(DOCSDIR, 'LICENSE.txt')
        SYSPLUGINSDIR = pkg_resources.resource_filename(
                                    req, os.path.join('gsdview', 'plugins'))

        del SHAREDIR, req

    except ImportError:
        import warnings
        warnings.warn(
            'Unable to locate the application data directory.\\n'
            'Please check yout installation.\\n'
            'If the error persists please file a bug report at:\\n'
            '  http://sourceforge.net/apps/trac/gsdview/wiki')

del PKGNAME, LIBDIR, os
'''

    def _striproot(self, path):
        install = self.get_finalized_command('install')

        if install.root and path.startswith(install.root):
            root = install.root.rstrip(os.sep)
            return path[len(root):]
        else:
            return path

    def install(self):
        installed = install_lib.install(self)

        # Retrieve datadir
        install = self.get_finalized_command('install')

        DATADIR = self._striproot(install.install_data)

        # Update the appsite.py file
        sitefile = 'appsite.py'
        libdir = os.path.join(self.install_dir, PKGNAME)
        filename = os.path.join(libdir, sitefile)
        log.info("updating %s -> %s", sitefile, libdir)

        from gsdview import appsite
        fp = open(filename, 'w')
        fp.write("'''%s'''" % appsite.__doc__)
        fp.write('''

# Automatically generated by setup.py.
# Please do not modify.

''')
        fp.write(self.stdinstall_schema % locals())
        fp.close()

        return installed

cmdclass['install_lib'] = InstallLib


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

datafiles = [
    (os.path.join('share', 'doc', PKGNAME), ['README.txt']),
    (os.path.join('share', 'doc', PKGNAME), ['LICENSE.txt']),
    #(os.path.join('share', 'doc', PKGNAME),
    #                [os.path.join('doc', 'GSDView.pdf')]),
]

HTMLPREFIX = os.path.join('share', 'doc', PKGNAME)

htmldocs = []
for root, dirs, files in os.walk(os.path.join('doc', 'html')):
    htmldocs = [os.path.join(root, filename) for filename in files]
    dstdir = os.path.join(HTMLPREFIX, root.split(os.sep, 1)[-1])
    datafiles.append((dstdir, htmldocs))

if os.name == 'posix':
    if platform.system() == 'FreeBSD':
        mandir = 'man'
    else:
        mandir = os.path.join('share', 'man')
    datafiles.append((os.path.join(mandir, 'man1'), ['doc/man/gsdview.1']))
    datafiles.append((
        os.path.join('share', 'applications'),
        ['gsdview.desktop']))
    datafiles.append((
        os.path.join('share', 'pixmaps'),
        [os.path.join('gsdview', 'images', 'GSDView.png')]))

kwargs['data_files'] = datafiles


if has_setuptools:
    packages = find_packages()
    kwargs.update(dict(
        install_requires=[
            'GDAL >= 1.6.1',
            'numpy >= 1.3.0',
            #'sip (>= 4.7.5)',
            #'PyQt >= 4.6'
        ],
        #extras_require = {},
        keywords='gsdview gdal',
        entry_points={
            'gui_scripts': ['gsdview = gsdview:main'],
            'setuptools.installation': ['eggsecutable = gsdview:main'],
        },
        include_package_data=True,
    ))
else:
    packages = [
        'exectools',
        'gsdtools',
        'gsdview',
        'gsdview.gdalbackend',
        'gsdview.plugins',
        'gsdview.plugins.overview',
        'gsdview.plugins.metadata',
        'gsdview.plugins.positiontracker',
        'gsdview.plugins.worldmap',
        'gsdview.plugins.zoom',
    ]

    if os.name == 'nt':
        kwargs['scripts'] = [os.path.join('scripts', 'gsdview.pyw')]
    else:
        kwargs['scripts'] = [os.path.join('scripts', 'gsdview')]

    kwargs['package_data'] = {
        'gsdview': ['ui/*.ui', 'images/*.svg', 'images/*.png'],
        'gsdview.gdalbackend': ['ui/*.ui', 'images/*.svg'],
        'gsdview.plugins.worldmap': ['images/*.jpg'],
    }


setup(
    name=PKGNAME,
    version=info.version,
    description=info.short_description,
    long_description=info.description,
    author=info.author,
    author_email=info.author_email,
    maintainer=info.author,
    maintainer_email=info.author_email,
    url=info.website,
    download_url=info.download_url,
    packages=packages,
    classifiers=[line for line in classifiers.split('\n') if line],
    license=info.license_type,
    platforms=['any'],
    requires=[
        'GDAL (>= 1.6.1)',
        'numpy (>= 1.3.0)',
        'sip (>= 4.7.5)',
        'PyQt4 (>= 4.6)',
    ],
    provides=[
        '%s (%d.%d.%d)' % ((PKGNAME,) + info.__version__),
        'exectools (%d.%d.%d)' % exectools_version,
        'gsdtools (%d.%d.%d)' % gsdtools_version,
    ],
    cmdclass=cmdclass,
    **kwargs
)
