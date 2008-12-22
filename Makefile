# Makefile

.PHONY: all docs resources

all: docs resources

docs:
	cd doc && make

resources: gsdview/gsdview_resources.py

%resources.py: resources.qrc images/*
	pyrcc4 -o $@ $<
