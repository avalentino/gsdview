# Makefile

.PHONY: all docs resources deb clean

all: docs resources

docs:
	cd doc && make html
	cd doc && make latex
	cd doc/build/latex && make

resources: gsdview/gsdview_resources.py

gsdview/gsdview_resources.py: resources.qrc images/*
	pyrcc4 -o $@ $<

clean:
	cd doc && $(MAKE) clean
	$(RM) -r build dist *~
	cd debian && $(RM) gsdview.* files pycompat stamp-makefile-build
	$(RM) python-build-stamp-*

deb: all
	dpkg-buildpackage -us -uc
