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

# -*- coding: UTF8 -*-

'''Utility functions and classes for GSDView.'''

__author__   = '$Author: valentino $'
__date__     = '$Date: 2008-11-25 17:02:03 +0100 (mar, 25 nov 2008) $'
__revision__ = '$Revision: 621 $'

import os
import sys

def default_workdir():
    if sys.platform[:3] == 'win':
        return 'C:\\'
    else:
        return os.path.expanduser('~')
