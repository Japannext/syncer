PROJECT_NAME = syncer

GIT = git
SED = sed

SHPROC = $(SHMISCDIR)/shproc
RCPATH ?= $(CURDIR)

TOPDIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

EXTLIBDIR = $(realpath $(TOPDIR)/..)
SHMISCDIR = $(EXTLIBDIR)/shmisc
