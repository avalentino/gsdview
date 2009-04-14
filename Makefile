### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

.PHONY: default docs html pdf resources clean sdist bdist deb rpmspec rpm

default: docs resources

docs: html pdf

html:
	cd doc && make html

pdf:
	cd doc && make latex
	cd doc/build/latex && make

resources: gsdview/gsdview_resources.py

gsdview/gsdview_resources.py: resources.qrc images/*
	pyrcc4 -o $@ $<

clean:
	cd doc && $(MAKE) clean
	$(RM) -r MANIFEST build dist *~
	$(RM) $(find . '*.pyc')
	cd debian && $(RM) -r gsdview gsdview.* files pycompat stamp-makefile-build
	$(RM) python-build-stamp-*

sdist: docs resources
	python setup.py sdist --manifest-only
	python setup.py sdist --force-manifest

bdist: sdist deb #rpm

deb: docs resources
	dpkg-buildpackage -us -uc

rpmspec:
	python setup.py bdist_rpm --spec-only

rpm: sdist
	#@sudo tools/build-rpm.sh
	python setup.py bdist_rpm

#debian/bestgui.1:: debian/manpage.xml
#	$(XP) -o $@ $(DB2MAN) $<
