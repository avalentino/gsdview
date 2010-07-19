# svn co http://svn.pyinstaller.org/trunk pyinstaller

GSDVIEWROOT=..
PYINSTALLERROOT=./pyinstaller
DISTROOT=../dist
BUNDLEROOT=../GSDView.app

.PHONY: onedir onefile clean html env

html:
	cd .. && $(MAKE) html

onedir: gsdview-onedir.spec html
	$(PYINSTALLERROOT)/Build.py $<
	#cp -rv $(DISTROOT)/gsdview/* $(BUNDLEROOT)/Contents/MacOS
	#mv $(BUNDLEROOT)/Contents/MacOS/Resources/* $(BUNDLEROOT)/Contents/Resources
	#$(RM) -r $(BUNDLEROOT)/Contents/MacOS/Resources

onefile: gsdview-onefile.spec html
	$(PYINSTALLERROOT)/Build.py $<

clean:
	$(RM) *.pyc logdict*.log warngsdview*.txt *~
	$(RM) -r $(GSDVIEWROOT)/dist/onefile
	$(RM) -r $(GSDVIEWROOT)/dist/gsdview
	$(RM) -r $(BUNDLEROOT)
	$(RM) -r build
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

