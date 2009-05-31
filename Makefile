### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

XP=xsltproc -''-nonet
DB2MAN=/usr/share/sgml/docbook/stylesheet/xsl/nwalsh/manpages/docbook.xsl

.PHONY: default docs html pdf man resources clean sdist bdist deb rpmspec rpm

default: docs resources

docs: html man
#docs: html pdf man

html:
	cd doc && make html

pdf: doc/GSDView.pdf
	cd doc && make latex
	cd doc/build/latex && make
	cp doc/build/latex/GSDView.pdf doc

man: debian/gsdview.1 debian/gsdviewer.1

debian/gsdview.1: debian/manpage.xml
	$(XP) -o $@ $(DB2MAN) $<

debian/gsdviewer.1: debian/gsdview.1
	cp debian/gsdview.1 debian/gsdviewer.1

resources: gsdview/resources.py \
           gsdview/splash_resources.py \
           gsdview/gdalbackend/resources.py \
           gsdview/plugins/worldmap/resources.py

gsdview/resources.py: images/resources.qrc images/*
	pyrcc4 -o $@ $<

gsdview/splash_resources.py: images/splash.qrc images/splash.svg
	pyrcc4 -o $@ $<

gsdview/gdalbackend/resources.py: \
                            gsdview/gdalbackend/images/resources.qrc \
                            gsdview/gdalbackend/images/*
	pyrcc4 -o $@ $<

gsdview/plugins/worldmap/resources.py: \
                            gsdview/plugins/worldmap/images/resources.qrc \
                            gsdview/plugins/worldmap/images/*
	pyrcc4 -o $@ $<


clean:
	cd doc && $(MAKE) clean
	$(RM) -r MANIFEST build dist
	$(RM) $(shell find . -name '*.pyc') $(shell find . -name '*~')
	cd debian && $(RM) -r gsdview gsdview.* gsdview*.1 files pycompat
	$(RM) python-build-stamp-* debian/stamp-makefile-build

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
