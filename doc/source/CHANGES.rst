..  :Source: doc/source/CHANGES.txt
    :Version: 0.7.0
    :Author: Antonio Valentino
    :Contact: antonio.valentino@tiscali.it
    :URL: http://gsdview.sourceforge.net
    :Copyright (C): 2008-2020 Antonio Valentino


ChangeLog
=========

Changes from 0.6.5 to 0.7.0 (in development)
--------------------------------------------

* Python 2 is no longer supported by GSDView.
* Implemented support for Python 3.x (closes: :issue:`76`).
  In order to run GSDView with Python 3 it is necessary to have GDAL >= 1.10.
* Now the reference Qt API used in GSDView is the one provided by the
  QtPy_ package.
* Now it is possible to toggle the full-screen mode using a tool-button or a
  keyboard shortcut.
* The exectools package now uses unicode buffers.
* Improved zoom control in case of high resolution mice or touchpads.
* Renewed sphinx_ theme. The HTML sphinx_ theme has been renewed.
  It is now based on the pydoctheme.
* The packaging scripts have been updated to run with the new
  PyInstaller_ 2.0.
* Removed stuff related Debian packaging (moved elsewhere).

.. _sphinx: http://sphinx-doc.org
.. _QtPy: https://github.com/spyder-ide/qtpy


Changes from 0.6.4 to 0.6.5 (13/11/2011)
----------------------------------------

* New gsdtools package providing extra utilities for geo-spatial data
  handling.  The gsdview.gsdtools module has been renamed into
  gsdview.imgutils.
* New functions for KML export and dataset area display on "Google Earth"
  and "Google Maps" (see :issue:`67`)
* Fixed workaround for incorrect GCP handling of ENVISAT stripline products
* Fixed global exception handler
* Fixed calls to external GDAL utilities by adding quotes to config options
* Fixed an unicode related issue in calls to gdal.SetConfigOption
* Improved PyInstaller_ packaging (upgreded to 1.5.1)
* Fix plugin loading when no plugin have to be loaded
* Support for PySide_ (closes :issue:`86`, see also :issue:`87`)

.. _PyInstaller: http://www.pyinstaller.org
.. _PySide: http://www.pyside.org


Changes from 0.6.3 to 0.6.4 (14/11/2010)
----------------------------------------

* Restored full compatibility wirh GDAL 1.6.x series
* Metadata export and printing (:issue:`84` and :issue:`85`)
* mainwin.py module renamed into mdi.py
* Set numeric locale to "C" at application startup in order to prevent
  issues with GDAL statistics serialization in virtual files
* Improved management of Qt4 items type
* Strongly improved GDAL dataset dialog
* Update to the new debian package format and new packaging standards


Changes from 0.6.2 to 0.6.3 (13/08/2010)
----------------------------------------

* Switch to the new PyQt4 signal/slot API (close :issue:`42`)
* Switch to PyQt4 API 2 for QString, QVariant etc (close :issue:`83`)
* All classes that inherit from Qt objects or widgets now can be initialized
  using keyword arguments for Qt properties and signals setup
* Improved overviews handling:

  - overview items are no more displayed in the treeview by default.
    It is possible to get the old behaviour by checking the appropriate
    flag in the preferences dialog (close :issue:`51`)
  - enabled action for overview computation in the dataset item context menu
  - the GDAL info dialog for raster bands has a new tab for overviews
    that also allows computation of new overviews (close :issue:`74`)

* Improved complex datasets support
* Improved sub-datasets handling
* Improved Radarsat2 support
* Now exectools.Qt4OutputHandler emits signals


Changes from 0.6.1 to 0.6.2 (20/07/2010)
----------------------------------------

* System info reporting improvements
* Fix system path setup in frozen environments
* Exectools package improved (close :issue:`57`)
* Always use (x,y,z) convention for geometric transforms
* Enabled complex selection on all lists and tables (close :issue:`68`)
* New button for stopping external tools (close :issue:`58`)
* Drop GDAL 1.5.x series: now GSDView requires GDAL 1.6.1 or higher
* Statistics and histograms computation now is fully asynchronous
  (close :issue:`45`).
  Configuration of custom histogram parameters in the GDAL info dialogs is
  temporary disabled.


Changes from 0.6.0 to 0.6.1 (09/05/2010)
----------------------------------------

* Basic support for RGB views (:issue:`18`)
* Use global exception hook to catch un-handled exceptions (close
  :issue:`28`).  An error dialog is showed and the application quits.
* New mouse manager component (:issue:`41`)
* Re-factoring of graphics items components
* New tool (plugin) for image stretching (close :issue:`54`)
* Strongly improved GDAL info dialogs (enhancement :issue:`39` and
  :issue:`49`).  Now dialogs show more info including:

  - image structure metadata
  - histograms (only in table form at the moment)
  - color tables
  - metadata for `IMAGE_STRUCTURE`, `SUBDATASETS` and `RPC` domains
    (standard domain was already available)

* Plugins re-factoring
* Auto detect GDAL framework binaries on Mac OS X (close :issue:`37`)
* Improved support for Mac OS X (:issue:`31`, :issue:`32`, :issue:`33`,
  :issue:`34`). None Qt >= 4.6.2 is required on Mac OS X.
* Reduced a bit the time required for datasets opening (see :issue:`29`)
* Improved the algorithm to determine the overview levels to compute at
  band opening time (see :issue:`40`)
* Now it is possible to pre-compile UI files into python modules and use
  generated modules to set the GUI up.
  If pre-compiled python forms are not available the GUI is set up using
  Qt UI files directly.
* Now use docutils for generating the manpage (:issue:`50`)
* Packaging using PyInstaller_ (:issue:`25`)
* Other bug fix (:issue:`38`, :issue:`48`, :issue:`53`)


Changes from 0.5.9 to 0.6.0 (24/08/2009)
----------------------------------------

* New plugin manager module (close :issue:`21`):

  - configurable search path for plugins
  - support for zip imports and eggs (**not tested**)
  - a new tab in preferences dialog allows to configure plugins manager
    via GUI

* Fixed bug in sub-datasets handling
* Improved debian packaging (close :issue:`20`)
* API reference added to documentation
* Resources handling re-factoring (close :issue:`23`)
* Initial support for PyInstaller_ packaging (:issue:`25`)
* Improved project layout: exectools in now an independent python package,
  no more a sub-package of gsdview (close :issue:`27`)
* `setuptools <https://pypi.python.org/pypi/setuptools>`_ support
  (close :issue:`24`)


Changes from 0.3.0 to 0.5.9 (10/05/2009)
----------------------------------------

* Complete application rewrite:

  - new architecture that allows multiple backends for actual data access
    (currently only GDAL backend is provided)
  - updated dataset browser with new contextual actions
  - now the application uses a Multiple Document Interface (MDI)
  - pluggable about dialog (plugins can add their own tab)
  - preference dialog
  - splash screen

* Improved GDAL configuration handling (without application re-spawning)
* New function for converting a numpy array into a QImage: now PyQwt is no
  more a strong dependency


Version 0.3.0 (18/05/2008)
--------------------------

First public release
