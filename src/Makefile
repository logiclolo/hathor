# $Id$
export HATHOR=$(shell pwd)
export HATHOR_VERSION=0.0.1.0

all:
	@make help

history: 
	@bin/gen_history

firmware: _tag _build_kernel _build_firmware _firmware_check history _firmware_release

release: _upload

clean:
	@rm -f output/* release/*

help:
	@bin/help

include lib/actions.mk

.PHONY: all history firmware release clean help
