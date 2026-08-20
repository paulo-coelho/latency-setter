PREFIX ?= /usr/local
SBINDIR ?= $(PREFIX)/sbin

install:
	install -m 755 latsetter.py $(SBINDIR)/latsetter

uninstall:
	rm -f $(SBINDIR)/latsetter

.PHONY: install uninstall