VERSION = $(shell cat $(TOPDIR)/VERSION)
COMMITID ?= $(shell $(GIT) rev-parse HEAD 2> /dev/null || echo "unknown")
