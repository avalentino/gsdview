# Makefile

.phony: resources

resurces: gsdview/gsdview_resources.py

%resources.py: resources.qrc images/*
	pyrcc4 -o $@ $<
