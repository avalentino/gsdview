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
	python $(PYINSTALLERROOT)/pyinstaller.py $<

onefile: gsdview-onefile.spec html
	python $(PYINSTALLERROOT)/pyinstaller.py $<

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
	git clone git://github.com/pyinstaller/pyinstaller.git
	#git clone -b master git://github.com/pyinstaller/pyinstaller.git

env: pyinstaller
	cd pyinstaller
	git pull
	#cd source && python waf configure build install
	#if ! [ -f gsdview_patches_applied ]; then \
	#	patch -b -N -p0 < ../patches/qt4-api2.patch;\
	#	touch gsdview_patches_applied;\
	#fi

