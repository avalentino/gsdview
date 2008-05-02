=======
GSDView
=======

:Source: README.txt
:Version: 0.3
:Author: Antonio Valentino
:Contact: a_valentino@users.sf.net
:URL: http://gsdview.sourceforge.net
:Revision: $Revision: 778 $
:Date: $Date: 2008-04-12 12:45:09 +0200 (sab, 12 apr 2008) $
:License: `GNU General Public License`__ (GPL)
:Copyright (C): 2008 Antonio Valentino <a_valentino@users.sf.net>

__ http://www.gnu.org/licenses/gpl.html

Intoduction
===========

@TBW

Downloads
=========

@TBW

Requirements
============

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

Ubuntu
------

::

  $ sudo apt-get python-qt4 python-qwt5-qt4  python-gdal gdal-bin python-numpy python-scipy

gdal 1.4.4

::
    Traceback (most recent call last):
      File "/home/antonio/projects/gsdview-compat/qt4support.py", line 57, in aux
        func(*args, **kwargs)
      File "plugins/gdal_band_overview/band_overview.py", line 101, in setBand
        data = ovrBand.ReadAsArray()
      File "/usr/lib/python2.5/site-packages/gdal.py", line 871, in ReadAsArray
        buf_xsize, buf_ysize, buf_obj )
      File "/usr/lib/python2.5/site-packages/gdalnumeric.py", line 181, in BandReadAsArray
        buf_xsize, buf_ysize, datatype, buf_obj )
    TypeError: Unaligned buffer
    Traceback (most recent call last):
      File "gsdview.py", line 438, in openRasterBand
        data = ovrBand.ReadAsArray()
      File "/usr/lib/python2.5/site-packages/gdal.py", line 871, in ReadAsArray
        buf_xsize, buf_ysize, buf_obj )
      File "/usr/lib/python2.5/site-packages/gdalnumeric.py", line 181, in BandReadAsArray
        buf_xsize, buf_ysize, datatype, buf_obj )
    TypeError: Unaligned buffer


Installation
============

@TBW

License
=======

@TBW
