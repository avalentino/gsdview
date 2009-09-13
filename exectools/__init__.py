### Copyright (C) 2006-2009 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of exectools.

### This module is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This module is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this module; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

__version__ = (0,5,0)
version = '.'.join(map(str, __version__))

from exectools import *
from subprocess2 import *

__all__ = ['EX_OK', 'BaseOStream', 'OFStream', 'BaseOutputHandler',
           'BaseToolController', 'ToolDescriptor', 'GenericToolDescriptor']
__all__.extend(subprocess2.__all__)
