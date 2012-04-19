# $Id$
export HATHOR=.
export HATHOR_VERSION=0.0.1.0

all:
	@make help

history: 
	@bin/gen_history

firmware: _tag _build_kernel _build_firmware _firmware_check _firmware_release

release: _upload

clean:
	@rm -f output/*

help:
	@bin/help

_tag: 
	@bin/firmware_tag_create

_build_kernel:
	@bin/firmware_build kernel

_build_firmware:
	@bin/firmware_build firmware

_firmware_check:
	@bin/firmware_compare

_firmware_release: 
	@bin/firmware_prerelease

_upload: product/history.txt product/firmware
	@bin/rt_ticket_send

.PHONY: all history firmware _build_firmware _tag _build_kernel check_firmware _firmware_release _upload clean help
