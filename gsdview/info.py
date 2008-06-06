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

'''Package info.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__revision__ = '$Revision$'
__version__ = (0,3,0)

__all__ = ['name', 'version', 'short_description', 'description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label']

import sys

name = 'GSDView'
version = '0.3a'

short_description = 'Geo-Spatial Data Viewer'
description = '''GSDView (Geo-Spatial Data Viewer) is a lightweight
viewer for geo-spatial data and products.
It is written in python and Qt4 and it is mainly intended to be a graphical
frotend for the GDAL library and tools.
GSDView is modular and has a simple plug-in architecture.

'''

author = ('Antonio Valentino',)
author_email = ('a_valentino@users.sf.net',)
copyright = 'Copytight (C) 2008 %s <%s>' % (author, author_email)
#license = _get_license()
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website

#artists = None
#documenters = ('AV',)
#thanks = None
#translator_credits = None

from PyQt4 import QtCore

all_versions = (
    #'%s v. %s (http://earth.esa.int/services/best)' % (binName, bestVersion),
    'Python v. %s (www.python.org)' % '.'.join(map(str,sys.version_info[:3])),
    'PyQt4 v. %s (http://www.riverbankcomputing.co.uk/pyqt/)' % QtCore.PYQT_VERSION_STR,            # @TODO: check
    'Qt v. %s (http://www.trolltech.com/qt/)' % QtCore.QT_VERSION_STR,  # @TODO: check
    'GDAL v. %s (http://www.gdal.org)' % '???', # @TODO: complete
)

