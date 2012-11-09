# $Id: Makefile 110756 2012-04-25 02:10:32Z klaymen $
export HATHOR=$(shell pwd)

all:
	@make help

history: 
	@bin/gen_history

# ordinary firmware release flow
firmware: _doctor_check_config _tag _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
firmware-skip-kernel: _doctor_check_config _tag _build_firmware _prepare _firmware_check history _firmware_prerelease
release: _doctor_check_config _upload

# sample firmwar release flow
sample: _doctor_check_config _tag_sample _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
sample-skip-kernel: _doctor_check_config _tag_sample _build_firmware _prepare _firmware_check history _firmware_prerelease
release-sample: _doctor_check_config _upload_sample
	
doctor: 
	@bin/doctor

doctor-again:
	@bin/doctor -f 

clean:
	@rm -rf output/${PRODUCTVER}

cleanall: clean
	@rm -rf release/${PRODUCTVER}

help:
	@bin/help


include lib/actions.mk

.PHONY: all history firmware release clean help
