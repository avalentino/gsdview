# svn co http://svn.pyinstaller.org/trunk pyinstaller

GSDVIEWROOT=..
PYINSTALLERROOT=./pyinstaller

.PHONY: onedir onefile clean html

html:
	cd .. && $(MAKE) html

onedir: gsdview-onedir.spec html
	$(PYINSTALLERROOT)/Build.py $<

onefile: gsdview-onefile.spec html
	$(PYINSTALLERROOT)/Build.py $<

clean:
	$(RM) *.pyc logdict*.log warngsdview*.txt +~
	$(RM) -r $(GSDVIEWROOT)/dist/onefile
	$(RM) -r $(GSDVIEWROOT)/dist/gsdview
	$(RM) -r build
	#if [ -d ../dist ]; then rmdir --ignore-fail-on-non-empty ../dist; fi

