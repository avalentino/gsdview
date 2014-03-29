..  =======
    GSDView
    =======

    :Source: README.txt
    :Version: 0.7.0
    :Author: Antonio Valentino
    :Contact: antonio.valentino@tiscali.it
    :URL: http://gsdview.sourceforge.net
    :Revision: $Revision$
    :Date: $Date$
    :License: `GNU General Public License`__ (GPL)
    :Copyright (C): 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

    __ GPL_


Introduction
============

GSDView (Geo-Spatial Data Viewer) Open Edition is a lightweight viewer for
geo-spatial data and products.
It is written in python_ and Qt4_ and it is mainly intended to be a graphical
front-end for the GDAL__ library and tools.
GSDView is modular and has a simple plug-in architecture.

.. note:: two editions of GSDView currently exist:

    - an *open source* version named `GSDView Open Edition`_ that is freely
      available (GPL2) and provides only very basic features
    - a GSDView Pro Edition that is non free and provides a larger number
      of features (including image analysis tools and integration components
      for external image processing tools)


.. _Python: https://www.python.org
.. _Qt4: http://qt-project.org
.. _`GSDView Open Edition`: http://gsdview.sourceforge.net
__ gdal_


Downloads
=========

Please refer to the `SourceForge project page`_.

.. _`SourceForge project page`: http://sourceforge.net/projects/gsdview


Requirements
============

In order to run GSDView you should have the following software installed:

* Python_ 2.6 or higher (including Python 3.x)
* SIP_ 4.7.5 or higher
* PyQt4_ 4.6 or higher
* numpy_ 1.3.0  or higher
* gdal_ 1.6.1 or higher

In replacement of PyQt4_ an SIP_ it is possible to use:

* PySide_ 1.0.4 or higher

.. _SIP: http://www.riverbankcomputing.co.uk/software/sip
.. _PyQt4: http://www.riverbankcomputing.co.uk/software/pyqt
.. _numpy: http://www.numpy.org
.. _gdal: http://www.gdal.org
.. _PySide: http://www.pyside.org

.. note:: in order to run GSDView with Python 3.x GDAL >= 1.10 is required.

.. hint::

   Ubuntu_ and Debian_ users can resolve all dependencies by running the
   following command as superuser::

     # apt-get install python-qt4 python-gdal gdal-bin

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
   installation** by simply running the following command in the package
   root::

    $ python run.py

.. note::

   Windows_\ :sup:`TM` users can **run GSDView without installation** by
   double-clicking on ``gsdview.pyw`` file.

   If it doesn't exist you can get it by making a copy of the
   ``run.py`` file and renaming it ``run.pyw``.

.. _Windows: http://windows.microsoft.com


License
=======

GSDView is released under the terms of the `GNU General Public License`__
version 2.

__ GPL_
.. _GPL: http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
