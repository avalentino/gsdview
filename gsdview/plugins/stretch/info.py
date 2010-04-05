# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

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

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2010/02/14 12:21:23 $'
__revision__ = '$Revision: 003973572867 $'
__version__  = (0,6,0)
__requires__ = []

__all__ = ['name', 'version', 'short_description', 'description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label']


name = 'stretch'
version = '.'.join(map(str, __version__))

short_description = 'Image stretch control for GSDView.'
description = '''The stretch plugin provides a control dialog to modify
the image stretch (pixel values resacling).
The plugin also installs a menu entry and a toolbar button.

'''

author = 'Antonio Valentino'
author_email = 'a_valentino@users.sf.net'
copyright = 'Copyright (C) 2008-2010 %s <%s>' % (author, author_email)
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website
