# $Id$
export HATHOR=.

all:

history: build_firmware
	@bin/gen_history

build_firmware: tag build_kernel check_firmware
	@bin/firmware_build firmware

tag: 
	@bin/firmware_tag_create

build_kernel:
	@bin/firmware_build kernel

check_firmware:
	@bin/compare_firmware
	@bin/firmware_prelease

upload: product/history.txt product/firmware
	@bin/rt_ticket_send

clean:
	@rm -f output/*

help:
	@bin/help

.PHONY: history upload clean tag all build_firmware build_kernel help
