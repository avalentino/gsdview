### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

RST2MAN=rst2man.py

.PHONY: default docs html pdf man clean cleanall sdist bdist deb rpmspec rpm ui

default: docs

docs: html man
#docs: html pdf man

html:
	cd doc && make html

pdf: doc/GSDView.pdf
	cd doc && make latex
	cd doc/build/latex && make
	cp doc/build/latex/GSDView.pdf doc

man: debian/gsdview.1

debian/gsdview.1: debian/manpage.rst
	$(RST2MAN) $< $@

clean:
	cd doc && $(MAKE) clean
	$(RM) -r MANIFEST build dist gsdview.egg-info
	$(RM) $(shell find . -name '*.pyc') $(shell find . -name '*~')
	$(RM) -r debian/gsdview debian/python-module-stampdir
	$(RM) debian/gsdview.* debian/gsdview*.1 debian/files debian/pycompat \
		  debian/python-module-stampdir
	$(RM) python-build-stamp-*
	$(MAKE) -C pkg clean

sdist: docs
	python setup.py sdist

# Not available in setuptools (??)
#	python setup.py sdist --manifest-only
#	 python setup.py sdist --force-manifest

bdist: sdist deb

deb: docs
	dpkg-buildpackage -us -uc

rpmspec:
	python setup.py bdist_rpm --spec-only

rpm: sdist
	#@sudo tools/build-rpm.sh
	python setup.py bdist_rpm

#debian/bestgui.1:: debian/manpage.xml
#	$(XP) -o $@ $(DB2MAN) $<

UIFILES = $(wildcard gsdview/ui/*.ui) $(wildcard gsdview/gdalbackend/ui/*.ui)
PYUIFILES = $(patsubst %.ui,%.py,$(UIFILES))

ui: $(PYUIFILES)
	touch gsdview/ui/__init__.py
	touch gsdview/gdalbackend/ui/__init__.py

%.py: %.ui
	pyuic4 -x $< -o $@

cleanall: clean
	$(RM) $(PYUIFILES)
	$(RM) gsdview/ui/__init__.py gsdview/gdalbackend/ui/__init__.py
