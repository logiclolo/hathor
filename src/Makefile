# $Id$
export HATHOR=.
export HATHOR_VERSION=1.0.0.0

all:
	@make help

history: 
	@bin/gen_history

firmware: tag build_kernel build_firmware firmware_check firmware_release

release: upload

tag: 
	@bin/firmware_tag_create

build_kernel:
	@bin/firmware_build kernel

build_firmware:
	@bin/firmware_build firmware

firmware_check:
	@bin/firmware_compare

firmware_release: 
	@bin/firmware_prerelease

upload: product/history.txt product/firmware
	@bin/rt_ticket_send

clean:
	@rm -f output/*

help:
	@bin/help

# help_firmware:
#     @bin/help firmware

# help_history:
#     @bin/help history

# help_release:
#     @bin/help release

.PHONY: all history firmware build_firmware tag build_kernel check_firmware firmware_release upload clean help
