# $Id: Makefile 110756 2012-04-25 02:10:32Z klaymen $
export HATHOR=$(shell pwd)

all:
	@make help

history: 
	@bin/gen_history

# ordinary firmware release flow
firmware: doctor_check_config _tag _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
release: doctor_check_config _upload

# sample firmwar release flow
sample: doctor_check_config _tag_sample _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
release-sample: doctor_check_config _upload_sample
	
doctor: 
	@bin/doctor

doctor_check_config:
	@bin/doctor_check_config

clean:
	@rm -rf output/${PRODUCTVER}

cleanall: clean
	@rm -rf release/${PRODUCTVER}

help:
	@bin/help


include lib/actions.mk

.PHONY: all history firmware release clean help
