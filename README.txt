=======
GSDView
=======

:Source: README.txt
:Version: 0.3
:Author: Antonio Valentino
:Contact: a_valentino@users.sf.net
:URL: http://gsdview.sourceforge.net
:Revision: $Revision$
:Date: $Date$
:License: `GNU General Public License`__ (GPL)
:Copyright (C): 2008 Antonio Valentino <a_valentino@users.sf.net>

__ http://www.gnu.org/licenses/gpl.html


Introduction
============

GSDView (Geo-Spatial Data Viewer) is a lightweight viewer for geo-spatial
data and products.
It is written in python and Qt4 and it is mainly intended to be a graphical
frontend for the GDAL library and tools.
GSDView is modular and has a simple plug-in architecture.

At the moment GSDView is at a very early development stage.

Downloads
=========

http://sourceforge.net/projects/gsdview


Requirements
============

In order to run GSDView you should have the following software installed:

* Python_ 2.5 or higher
* PyQt_ 4.0  or higher
* PyQwt_ 5.0  or higher
* numpy_ 1.0.4  or higher
* scipy_ 0.6  or higher
* gdal_ 1.4.4 or higher

.. _Python: http://www.python.org
.. _PyQt: http://www.riverbankcomputing.co.uk
.. _PyQwt: http://pyqwt.sourceforge.net
.. _numpy: http://www.numpy.org
.. _scipy: http://www.scipy.org
.. _gdal: http://www.gdal.org


Ubuntu/Debian
-------------

Ubuntu and Debian users can resolve all dependencies by running the
following command as superuser::

  # apt-get python-qt4 python-qwt5-qt4  python-gdal gdal-bin python-numpy python-scipy


Installation
============

Uncompress the distribution package::

  $ tar xvfz gsdview-X.YY.tar.gz
  
From the package directory run the following command as superuser::

  # python setup.py install

You can also install GSDView in a custom location::

    # python setup.py install --prefix=<PATH_TO_INSTALL_DIR>


License
=======

GSDview is released under the terms of the `GNU General Public License`__
version 2.
See the LICENSE.txt file.

__ GPL_

.. _GPL: http://www.gnu.org/licenses/gpl.html

.. raw:: html

   <a href="http://sourceforge.net">
      <img src="http://sflogo.sourceforge.net/sflogo.php?group_id=226458&amp;type=5" width="210" height="62" border="0" alt="SourceForge.net Logo" />
   </a>

