# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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

__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date: 2011-07-29 21:22:09 +0200 (ven, 29 lug 2011) $'
__revision__ = '$Revision: $'
__version__ = (0, 6, 5)
__requires__ = ['gdalbackend']

__all__ = ['name', 'version', 'short_description', 'description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label']


name = 'gsdtoolsui'
version = '.'.join(map(str, __version__))

short_description = 'UI front-end for GSDTools'
description = '''The GSDTools plugin provides a simple UI front-end to the
GSDTools collection of libraries and command line utilities.

'''

author = 'Antonio Valentino'
author_email = 'a_valentino@users.sf.net'
copyright = 'Copyright (C) 2008-2011 %s <%s>' % (author, author_email)
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website
