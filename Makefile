# $Id: Makefile 110756 2012-04-25 02:10:32Z klaymen $
export HATHOR=$(shell pwd)
export HATHOR_VERSION=1.0.0.0

all:
	@make help

history: 
	@bin/gen_history

firmware: _check_healthiness _tag _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease

release: _check_healthiness _upload

doctor: 
	@bin/doctor

clean:
	@rm -rf output/${PRODUCTVER}

cleanall: clean
	@rm -rf release/${PRODUCTVER}

help:
	@bin/help

include lib/actions.mk

.PHONY: all history firmware release clean help
