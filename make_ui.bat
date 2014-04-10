set PYUIC=python C:\Python27\Lib\site-packages\PySide\scripts\uic.py

echo "" >> gsdview\ui\__init__.py
echo "" >> gsdview\gdalbackend\ui\__init__.py
echo "" >> gsdview\plugins\stretch\ui\__init__.py

%PYUIC% -x gsdview\ui\aboutdialog.ui     -o gsdview\ui\aboutdialog.py
%PYUIC% -x gsdview\ui\exceptiondialog.ui -o gsdview\ui\exceptiondialog.py
%PYUIC% -x gsdview\ui\general-page.ui    -o gsdview\ui\general-page.py
%PYUIC% -x gsdview\ui\plugininfo.ui      -o gsdview\ui\plugininfo.py
%PYUIC% -x gsdview\ui\pluginmanager.ui   -o gsdview\ui\pluginmanager.py
%PYUIC% -x gsdview\ui\preferences.ui     -o gsdview\ui\preferences.py
%PYUIC% -x gsdview\gdalbackend\ui\banddialog.ui    -o gsdview\gdalbackend\ui\banddialog.py
%PYUIC% -x gsdview\gdalbackend\ui\datasetdialog.ui -o gsdview\gdalbackend\ui\datasetdialog.py
%PYUIC% -x gsdview\gdalbackend\ui\gdalinfo.ui      -o gsdview\gdalbackend\ui\gdalinfo.py
%PYUIC% -x gsdview\gdalbackend\ui\gdalpage.ui      -o gsdview\gdalbackend\ui\gdalpage.py
%PYUIC% -x gsdview\gdalbackend\ui\histoconfig.ui   -o gsdview\gdalbackend\ui\histoconfig.py
%PYUIC% -x gsdview\gdalbackend\ui\metadata.ui      -o gsdview\gdalbackend\ui\metadata.py
%PYUIC% -x gsdview\gdalbackend\ui\overview.ui      -o gsdview\gdalbackend\ui\overview.py
%PYUIC% -x gsdview\plugins\stretch\ui\doubleslider.ui  -o gsdview\plugins\stretch\ui\doubleslider.py
%PYUIC% -x gsdview\plugins\stretch\ui\stretchdialog.ui -o gsdview\plugins\stretch\ui\stretchdialog.py
