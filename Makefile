# Makefile

.PHONY: all docs resources

all: docs resources

docs:
	cd doc && make html
	cd doc && make latex
	cd doc/build/latex && make

resources: gsdview/gsdview_resources.py

gsdview/gsdview_resources.py: resources.qrc images/*
	pyrcc4 -o $@ $<
