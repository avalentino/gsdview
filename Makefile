### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

.PHONY: default docs html pdf man clean distclean sdist bdist deb rpmspec rpm ui

default: html

docs: html pdf man

html:
	$(MAKE) -C doc html

pdf: doc/GSDView.pdf

doc/GSDView.pdf:
	$(MAKE) -C doc latexpdf
	cp doc/build/latex/GSDView.pdf doc

man: debian/gsdview.1

debian/gsdview.1: doc/gsdview.1
	cd debian && ln -fs ../doc/gsdview.1

doc/gsdview.1:
	$(MAKE) -C doc man

sdist: ui docs
	python setup.py sdist --formats=gztar,zip

# Not available in setuptools (??)
#	@python setup.py sdist --manifest-only
#	@python setup.py sdist --force-manifest

bdist: deb rpm

deb: ui docs sdist
	mkdir -p build/deb
	cp dist/gsdview-?.?.*.tar.gz build/deb
	tar -C build/deb -xvzf build/deb/gsdview-?.?.*.tar.gz
	rename s/.tar.gz/.orig.tar.gz/ build/deb/gsdview-?.?.*.tar.gz
	rename s/gsdview-/gsdview_/ build/deb/gsdview-?.?.*.orig.tar.gz
	cd build/deb/gsdview-?.?.* && debuild -us -uc
	mv build/deb/gsdview_?.?.* dist

rpmspec:
	python setup.py bdist_rpm --spec-only

rpm: sdist
	python setup.py bdist_rpm


UIFILES = $(wildcard gsdview/ui/*.ui)\
          $(wildcard gsdview/gdalbackend/ui/*.ui)\
          $(wildcard gsdview/plugins/stretch/ui/*.ui)
PYUIFILES = $(patsubst %.ui,%.py,$(UIFILES))

ui: $(PYUIFILES)
	touch gsdview/ui/__init__.py
	touch gsdview/gdalbackend/ui/__init__.py
	touch gsdview/plugins/stretch/ui/__init__.py

%.py: %.ui
	pyuic4 -x $< -o $@

clean:
	$(MAKE) -C doc clean
	$(RM) -r MANIFEST gsdview.egg-info
	$(RM) -r dist build
	find . -name '*.py[c,o]' -delete
	find . -name '*.bak' -delete
	find . -name '*~' -delete
	$(RM) -r debian/gsdview debian/python-module-stampdir
	$(RM) debian/gsdview.* debian/gsdview*.1 debian/files debian/pycompat \
          debian/python-module-stampdir
	$(RM) python-build-stamp-*
	$(MAKE) -C pkg clean

distclean: clean
	$(RM) doc/gsdview.1
	$(RM) $(PYUIFILES)
	$(RM) gsdview/ui/__init__.py gsdview/gdalbackend/ui/__init__.py \
          gsdview/plugins/stretch/ui/__init__.py
	$(RM) -r pkg/pyinstaller
