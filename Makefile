### :Source: Makefile
### :Author: Antonio Valentino
### :Contact: a_valentino@users.sf.net
### :URL: http://gsdview.sourceforge.net
### :Revision: $Revision$
### :Date: $Date$

XP=xsltproc -''-nonet
DB2MAN=/usr/share/sgml/docbook/stylesheet/xsl/nwalsh/manpages/docbook.xsl

.PHONY: default docs html pdf man clean sdist bdist deb rpmspec rpm

default: docs

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

clean:
	cd doc && $(MAKE) clean
	$(RM) -r MANIFEST build dist gsdview.egg-info
	$(RM) $(shell find . -name '*.pyc') $(shell find . -name '*~')
	cd debian && $(RM) -r gsdview gsdview.* gsdview*.1 files pycompat
	$(RM) python-build-stamp-* debian/stamp-makefile-build
	cd pkg && $(MAKE) clean

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
