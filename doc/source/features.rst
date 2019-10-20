..  :Source: doc/source/features.txt
    :Version: 0.7.0
    :Author: Antonio Valentino
    :Contact: antonio.valentino@tiscali.it
    :URL: http://gsdview.sourceforge.net
    :Copyright (C): 2008-2015 Antonio Valentino


Features
========

A list of the main features of `GSDView Open Source Edition`_ v. |release|.

.. _`GSDView Open Source Edition`:  http://gsdview.sourceforge.net


================================================ =======
Basic features                                   Status
================================================ =======
open arbitrary sized images                         X
open multiple datasets (with MDI interface)         X
zoom in/out                                         X
fast scroll/pan                                     X
mouse modes handling                                X
printing                                            --
print/export metadata                               X
RGB display                                         X
arbitrary large raster data display                 X
vector data display                                 --
================================================ =======

================================================ =======
Architecture                                     Status
================================================ =======
plug-in architecture                                X
plug-in manager                                     X
advanced external tool controller                   X
multiple back-ends support                          X
================================================ =======

================================================ =======
Components                                       Status
================================================ =======
progress bar                                        X
preferences dialog                                  X
bug-report dialog                                   X
plug-ins management GUI                             X
datasets browser                                    X
context menu for GDAL objects                       X
info dialogs for GDAL objects                       X
overview panel with view port box                   X
log panel                                           X
logging to file                                     --
meta-data panel                                     X
position indicator on world map                     X
mouse pointer position indicator (row, col)         X
mouse pointer geographic position indicator         X
================================================ =======

================================================ =======
Tools                                            Status
================================================ =======
image stretching (pixel value scaling)              X
selection tool                                      --
rotation tool                                       --
draw tools                                          --
snapshot generation                                 --
export raster data footprints to KML                X
meta-data dump                                      X
meta-data print                                     X
export GCPs in vector format                        X
================================================ =======

================================================ =======
Processing                                       Status
================================================ =======
run processing tasks in external processes          X
processing tasks can be stopped by the user         X
support for standard GDAL tools                     --
band arithmetic                                     --
kernel filtering                                    --
extra processing tools                              --
================================================ =======

================================================ =======
GDAL                                             Status
================================================ =======
advanced GDAL configuration handling                X
automatic pyramids computation                      X
advanced sub-datasets handling                      X
dataset creation/editing                            --
raster bands creation/editing                       --
meta-data bands creation/editing                    --
GCPs bands creation/editing                         --
portion extraction                                  --
creation of warped datasets                         --
================================================ =======

================================================ =======
Formats                                          Status
================================================ =======
all raster formats supported by GDAL                X
all vector formats supported by OGR                 --
================================================ =======

================================================ =======
Platforms                                        Status
================================================ =======
GNU Linux/Unix                                      X
MS Windows XP (32 bit)                              X
MS Windows Vista                                    --
MS Windows 7                                        --
Mac OS X                                            X
================================================ =======

================================================ =======
Distribution                                     Status
================================================ =======
Windows installer                                   --
Debian packages                                     X
RPM packages                                        X
standalone binary for GNU/Linux                  [#pkg]_
standalone binary for Mac OS X                      X
python egg                                       [#pkg]_
source code availability                            X
================================================ =======


.. rubric:: Footnotes

.. [#pkg] the package is delivered on request.


Legend
------

====== =====================================================
Symbol
====== =====================================================
  X    feature available
  --   feature not currently available
  NEW  the feature is available and it is a recent addition
====== =====================================================
