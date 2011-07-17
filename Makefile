### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

BUILDDIR    = build
DOCBUILDDIR = $(BUILDDIR)/sphinx
#SIGNKEYID = antonio.valentino@tiscai.it
DEBUILD_OPTIONS = -us -uc

.PHONY: default docs html pdf man clean distclean sdist bdist deb rpmspec rpm ui

default: html

docs: html pdf man

html:
	$(MAKE) -C doc html

pdf: doc/GSDView.pdf

doc/GSDView.pdf:
	$(MAKE) -C doc latexpdf
	cp $(DOCBUILDDIR)/latex/GSDView.pdf doc

man: debian/gsdview.1

debian/gsdview.1: doc/source/manpage.txt
	$(MAKE) -C doc man
	cp -f $(DOCBUILDDIR)/man/gsdview.1 $@
	#gzip -c $@ > $@.gz


sdist: ui docs
	python setup.py sdist --formats=gztar,zip

# Not available in setuptools (??)
#	python setup.py sdist --manifest-only
#	python setup.py sdist --force-manifest

bdist: deb rpm

deb: ui docs sdist
	mkdir -p $(BUILDDIR)/deb
	cp dist/gsdview-?.?.*.tar.gz build/deb
	tar -C $(BUILDDIR)/deb -xvzf $(BUILDDIR)/deb/gsdview-?.?.*.tar.gz
	rename s/.tar.gz/.orig.tar.gz/ $(BUILDDIR)/deb/gsdview-?.?.*.tar.gz
	rename s/gsdview-/gsdview_/ $(BUILDDIR)/deb/gsdview-?.?.*.orig.tar.gz
	cd $(BUILDDIR)/deb/gsdview-?.?.* && debuild $(DEBUILD_OPTIONS)
	mv $(BUILDDIR)/deb/gsdview_?.?.* dist

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
	$(MAKE) -C pkg clean
	$(RM) MANIFEST
	$(RM) -r build gsdview.egg-info
	-find . -name '*.py[co]' -delete
	-find . -name '*.bak' -delete
	-find . -name '*~' -delete
	$(RM) -r debian/gsdview debian/python-module-stampdir
	#$(RM) debian/gsdview.* debian/files debian/pycompat
	$(RM) python-build-stamp-*

distclean: clean
	$(MAKE) -C doc distclean
	$(MAKE) -C pkg distclean
	$(RM) -r dist
	$(RM) $(PYUIFILES)
	$(RM) gsdview/ui/__init__.py gsdview/gdalbackend/ui/__init__.py \
          gsdview/plugins/stretch/ui/__init__.py
