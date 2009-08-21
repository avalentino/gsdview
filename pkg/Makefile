GSDVIEWROOT=..
PYINSTALLERROOT=./pyinstaller

.PHONY: onedir onefile clean

onedir: gsdview-onedir.spec
	$(PYINSTALLERROOT)/Build.py $<

onefile: gsdview-onefile.spec
	$(PYINSTALLERROOT)/Build.py $<

clean:
	$(RM) *.pyc logdict*.log warngsdview*.txt +~
	$(RM) -r $(GSDVIEWROOT)/dist/onefile
	$(RM) -r $(GSDVIEWROOT)/dist/gsdview
	rmdir --ignore-fail-on-non-empty ../dist
	$(RM) -r $(GSDVIEWROOT)/build/pyi.*
	rmdir --ignore-fail-on-non-empty ../build

