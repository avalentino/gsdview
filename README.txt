..  =======
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

    __ GPL_


Introduction
============

GSDView (Geo-Spatial Data Viewer) is a lightweight viewer for geo-spatial
data and products.
It is written in python and Qt4 and it is mainly intended to be a graphical
front-end for the GDAL library and tools.
GSDView is modular and has a simple plug-in architecture.

At the moment GSDView is at a very early development stage.


Downloads
=========

Please refer to the `SourceForge project page`_.

.. _`SourceForge project page`: http://sourceforge.net/projects/gsdview


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

.. hint::

   Ubuntu_ and Debian_ users can resolve all dependencies by running the
   following command as superuser::

     # apt-get python-qt4 python-qwt5-qt4 python-gdal gdal-bin python-numpy python-scipy

.. _Ubuntu: http://www.ubuntu.com
.. _Debian: http://www.debian.org


Installation
============

Decompress the distribution package::

  $ tar xvfz gsdview-X.YY.tar.gz

From the package directory run the following command as superuser::

  # python setup.py install

You can also install GSDView in a custom location::

    # python setup.py install --prefix=<PATH_TO_INSTALL_DIR>


.. note::

   If you have all dependencies installed you can **run GSDView without
   installation** by simply running the following command in the package root::

    $ python gsdviewer


.. note::

   Windows_\ :sup:`TM` users can **run GSDView without installation** by
   double-clicking on ``gsdviewer.pyw`` file.

   If it doesn't exist you can get it by making a copy of the ``gsdviewer``
   file and renaming it ``gsdviewer.pyw``.

.. _Windows: http://www.microsoft.com/windows


License
=======

GSDview is released under the terms of the `GNU General Public License`__
version 2.

__ GPL_

.. _GPL: http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
