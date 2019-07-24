include Makefile.inc
include version.mk

BINS = syncer syncerd
VERSION_PY = version.py

all: $(BINS) $(VERSION_PY)

$(VERSION_PY): version.py.in
	@mkdir -p $(@D)
	$(SED) \
		-e s,%%VERSION%%,$(VERSION), \
		-e s,%%COMMITID%%,$(COMMITID), \
		-e s,%%BUILD_USER%%,$(shell whoami), \
		-e s,%%BUILD_HOST%%,$(shell hostname), \
		-e s,%%BUILD_PWD%%,$(shell pwd), \
		-e s,%%BUILD_DATE%%,$(shell date +%Y%m%d), \
		$< > $@

syncer: syncer.in
	$(SHPROC) -DRCPATH=$(RCPATH) -I$(SHMISCDIR) $< $@
	@chmod +x $@

syncerd: syncerd.py
	cat $< > $@
	@chmod +x $@

clean:
	rm -f $(VERSION_PY) $(BINS)
	find . -type f -name "*.pyc" -exec rm {} \;

tag:
	$(GIT) tag $(PROJECT_NAME)-$(VERSION) -m "Tagging $(VERSION) release"

.PHONY: all clean tag
