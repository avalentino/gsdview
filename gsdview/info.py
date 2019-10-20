# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US


"""Package info."""


import sys
import platform

import numpy as np

import qtpy
from qtpy import QtCore


__version__ = (0, 7, 0)

__all__ = ['name', 'version', 'short_description', 'description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label', 'all_versions', 'all_versions_str']

name = 'GSDView'
version = '.'.join(str(v) for v in __version__) + '.dev'

short_description = 'Geo-Spatial Data Viewer Open Source Edition'
description = '''GSDView (Geo-Spatial Data Viewer) is a lightweight
viewer for geo-spatial data and products.

It is written in python and Qt4 and it is mainly intended to be a graphical
frotend for the GDAL library and tools.

GSDView is modular and has a simple plug-in architecture.

'''

author = 'Antonio Valentino'
author_email = 'antonio.valentino@tiscali.it'
copyright = 'Copyright (C) 2008-2019 %s <%s>' % (author, author_email)
# license = _get_license()
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website
download_url = 'http://sourceforge.net/projects/gsdview/files'


all_versions = [
    ('GSDView', version, website),
    ('Python', '.'.join(
        map(str, sys.version_info[:3])), 'https://www.python.org'),
    ('Qt', QtCore.qVersion(), 'http://www.qt.io/'),
    ('numpy', np.version.version, 'http://www.numpy.org'),
]

if qtpy.API.startswith('pyqt'):
    import sip
    all_versions.append(('sip', sip.SIP_VERSION_STR,
                         'http://www.riverbankcomputing.co.uk/software/sip'))
    all_versions.append(('PyQt', QtCore.PYQT_VERSION_STR,
                         'http://www.riverbankcomputing.co.uk/software/pyqt'))
    try:
        from qtpy import Qsci
    except ImportError:
        pass
    else:
        all_versions.append((
            'QScintilla', Qsci.QSCINTILLA_VERSION_STR,
            'http://www.riverbankcomputing.co.uk/software/qscintilla'))

elif qtpy.API == 'pyside':
    import PySide
    all_versions.append(
        ('PySide', PySide.__version__, 'http://www.pyside.org'))

elif qtpy.API == 'pyside2':
    import PySide2
    all_versions.append(
        ('PySide2', PySide2.__version__, 'http://www.pyside.org'))

if platform.dist() != ('', '', ''):
    all_versions.append(('GNU/Linux', ' '.join(platform.dist()), ''))
elif platform.mac_ver() != ('', ('', '', ''), ''):
    all_versions.append(('Mac OS X', platform.mac_ver()[0],
                         'http://www.apple.com/macosx'))
elif platform.win32_ver() != ('', '', '', ''):
    all_versions.append(('Windows', platform.win32_ver()[0],
                         'http://www.microsoft.com/windows'))


def all_versions_str():
    return '\n'.join(
        '%s v. %s %s' % (sw, version_, '(%s)' % link if link else '')
        for sw, version_, link in all_versions)
