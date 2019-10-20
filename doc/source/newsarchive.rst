..  :Source: doc/source/newsarchive.txt
    :Version: 0.7.0
    :Author: Antonio Valentino
    :Contact: antonio.valentino@tiscali.it
    :URL: http://gsdview.sourceforge.net
    :Copyright (C): 2008-2015 Antonio Valentino


News archive
============

This page contains the complete news archive of the `GSDView project`__.

__ `GSDView project page`_

.. include:: latestnews.rst

:03/09/2012: SCM moved to Git_.

             The GSDView code is now maintained in a Git_ repository.

             Git_ is a modern and distributed SCM system that makes it easier
             for developers to manage the development process.

             All developers that have a checkout of the old SVN repository
             should make a fresh checkout.

:03/09/2012: The GSDView project moves to Allura_.

             The GSDView project on sourceforge.net has been converted to use
             the new Allura_ platform.

:13/11/2011: GSDView Open Source Edition v. 0.6.5 released.

             Fixed some compatibility issues with new PyQt4_ and SIP_
             versions.  Full support to PySide_ (>= 1.0.4).

             Please refer to :doc:`CHANGES` for more details.

:31/07/2011: GSDView now also works with PySide_

             Full support to PySide_ has been implemented.
             Now GSDView can optionally use PySide_ as Qt4_ bindings instead
             PyQt4_ and SIP_.

:24/07/2011: A new tentative package for Mac OS X

             A new tentative package for Mac OS X. It includes a beta
             version of GDSView 0.6.5.

             Feedback is very welcome.

:28/11/2010: GSDView Open v. 0.6.4 run on Fedora_ 14.

             In Fedora_ 14 it has been fixed a bug in GDAL packaging
             that caused a GSDView crash on startup.
             The (recently updated) RPM package now runs nicely on
             Fedora_ too.

:14/11/2010: GSDView Open Source Edition v. 0.6.4 released.

             This is an hot-fix release that restores the complete
             compatibility with GDAL 1.6.x series.

             Also some new feature have been added: see :doc:`CHANGES`.

:13/11/2010: Ubuntu packages now available via Launchpad.

             Source packages and pre-build binary packages for Ubuntu 10.10
             are now available via PPA (Personal Package Archive) on
             Launchpad_.

             The archive and instructions for usage are at the following URL:

             https://launchpad.net/~a.valentino/+archive/eotools

:13/08/2010: GSDView Open Source Edition v. 0.6.3 released.

             This release has been implemented a complete switch of the
             application to the new PyQt4_ API (new signal/slot handling,
             QString and QVariant are gone, etc.).
             For this reason GSDView now requires PyQt4_ v. 4.6 or newer.

             Also some new feature have been added: see :doc:`CHANGES`.

:20/07/2010: GSDView Open Source Edition v. 0.6.2 released.

             This release don't include big changes visible to the user.
             It introduces some important internal changes such as the switch
             to GDAL 1.6.x series and a new system for full asynchronous
             handling of computation tasks (including statistics and histogram
             computation).

:01/07/2010: GDAL 1.5.x series dropped.

             GDAL 1.6.x series introduced a lot of new interesting features
             and a better progress handling.
             Dropping 1.5.x series allow to use this new features in the
             `development branch`_ to make GSDView even better.

:09/05/2010: Binary package for `Mac OS X`_ released.

             The long waited binary package for `Mac OS X`_ is now available.
             The package provides a standalone executable of GSDView 0.6.1
             with a couple of micro-patches backported from trunk.

             While GSDView 0.6.1 is considered quite stable the package for
             `Mac OS X`_ is brand new and it is considered beta quality,
             so any kind of feedback is welcome.

:09/05/2010: GSDView Open Source Edition v. 0.6.1 released.

             This new release brings some major improvement to GSDView
             including basic support for RGB views, a new tool for image
             stretching and a new component for mouse modes handling.

             Also there is a new dialog that shows detailed info about
             application crashes and allow the user to submit bug reports.

:24/08/2009: GSDView Open Source Edition v. 0.6.0 released.

             With respect to the alpha version a serious bug in
             sub-datasets handling has been fixed.
             New component (PluginManager) for plugin management.
             It is configurable via preferences dialog.

:10/05/2009: GSDView Open Source Edition v. 0.6.0 alpha 1 released.

             Almost complete application re-write:
             new architecture that allows multiple data access backends
             (currently only GDAL backend is provided), updated dataset
             browser with new contextual actions, Multiple Document
             Interface (MDI), new preference dialog, improved GDAL
             configuration handling.

:30/08/2008: New Home Page.

             The project Home Page has been completely rewritten.
             Now the sphinx_ tool is used to generate the entire
             documentation set.

:18/05/2008: First public release available.

             The first public release of GSDView is available for download_
             on SourceForge_.

             This is still an alpha release with a minimal set of features.


.. _PyQt5: https://www.riverbankcomputing.com/software/pyqt
.. _PyQt4: https://www.riverbankcomputing.com/software/pyqt
.. _PySide: http://www.pyside.org
.. _Git: http://git-scm.com
.. _Allura: https://sourceforge.net/p/allura/wiki
.. _SIP: http://www.riverbankcomputing.co.uk/software/sip
.. _Qt4: http://qt-project.org
.. _Fedora: http://fedoraproject.org
.. _Launchpad: https://www.launchpad.net
.. _`development branch`: https://github.com/avalentino/gsdview
.. _`Mac OS X`: http://www.apple.com/osx
.. _`GSDView project page`: http://sourceforge.net/projects/gsdview
.. _download: http://sourceforge.net/projects/gsdview/files
.. _sphinx: http://sphinx-doc.org
.. _SourceForge: http://sourceforge.net
