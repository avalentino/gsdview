# svn co http://svn.pyinstaller.org/trunk pyinstaller

GSDVIEWROOT=..
PYINSTALLERROOT=./pyinstaller
DISTROOT=../dist
ONEDIRBUNDLE=$(DISTROOT)/GSDView.app
ONEFILEBUNDLE=$(DISTROOT)/onefile/GSDView.app

.PHONY: onedir onefile clean distclean html env

html:
	cd .. && $(MAKE) html

onedir: gsdview-onedir.spec html
	$(PYINSTALLERROOT)/Build.py $<
	if [ -d $(ONEDIRBUNDLE) ]; then \
		mv $(ONEDIRBUNDLE)/Contents/MacOS/Resources/* $(ONEDIRBUNDLE)/Contents/Resources; \
		$(RM) -r $(ONEDIRBUNDLE)/Contents/MacOS/Resources; \
		cp GSDView.icns $(ONEDIRBUNDLE)/Contents/Resources; \
	fi

onefile: gsdview-onefile.spec html
	$(PYINSTALLERROOT)/Build.py $<
	if [ -d $(ONEFILEBUNDLE) ]; then \
		cp -rv /Library/Frameworks/QtGui.framework/Resources/qt_menu.nib $(ONEFILEBUNDLE)/Contents/Resources; \
		cp GSDView.icns $(ONEFILEBUNDLE)/Contents/Resources; \
	fi

clean:
	$(RM) *.pyc logdict*.log warngsdview*.txt *~
	$(RM) -r build
	$(RM) -r $(ONEDIRBUNDLE) $(ONEFILEBUNDLE)
	$(RM) -r $(GSDVIEWROOT)/dist/onefile
	$(RM) -r $(GSDVIEWROOT)/dist/gsdview
	#if [ -d ../dist ]; then rmdir --ignore-fail-on-non-empty ../dist; fi

distclean: clean
	$(RM) -r pyinstaller

pyinstaller:
	svn co http://svn.pyinstaller.org/trunk pyinstaller

env: pyinstaller
	svn up pyinstaller
	#cd pyinstaller/source && python waf configure build install
	if ! [ -f pyinstaller/Build.py.orig ]; then \
		cd pyinstaller;\
		patch -b -N -p0 < ../patches/qt4-api2.patch;\
	fi

