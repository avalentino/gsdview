# svn co http://svn.pyinstaller.org/trunk pyinstaller

GSDVIEWROOT=..
PYINSTALLERROOT=./pyinstaller
DISTROOT=../dist
BUNDLEROOT=Macgsdview.app

.PHONY: onedir onefile clean html env

html:
	cd .. && $(MAKE) html

onedir: gsdview-onedir.spec html
	$(PYINSTALLERROOT)/Build.py $<
	if [ -d $(BUNDLEROOT) ]; then \
		cp -rv $(DISTROOT)/gsdview/* $(BUNDLEROOT)/Contents/MacOS; \
		mv $(BUNDLEROOT)/Contents/MacOS/Resources/* $(BUNDLEROOT)/Contents/Resources; \
		$(RM) -r $(BUNDLEROOT)/Contents/MacOS/Resources; \
		cp gsdview.png $(BUNDLEROOT)/Contents/Resources; \
	fi

onefile: gsdview-onefile.spec html
	$(PYINSTALLERROOT)/Build.py $<
	if [ -d $(BUNDLEROOT) ]; then \
		cp -rv /Library/Frameworks/QtGui.framework/Resources/qt_menu.nib $(BUNDLEROOT)/Contents/Resources; \
		cp gsdview.png $(BUNDLEROOT)/Contents/Resources; \
	fi

clean:
	$(RM) *.pyc logdict*.log warngsdview*.txt *~
	$(RM) -r $(GSDVIEWROOT)/dist/onefile
	$(RM) -r $(GSDVIEWROOT)/dist/gsdview
	$(RM) -r $(BUNDLEROOT)
	$(RM) -r build Macgsdview.app
	#if [ -d ../dist ]; then rmdir --ignore-fail-on-non-empty ../dist; fi

pyinstaller:
	svn co http://svn.pyinstaller.org/trunk pyinstaller

env: pyinstaller
	svn up pyinstaller
	cd pyinstaller && sh make-linux.sh python
	if ! [ -f pyinstaller/Build.py.orig ]; then \
		cd pyinstaller && patch -b -N < ../patches/osx-python-image.patch;\
	fi
	cd pyinstaller && python Configure.py

