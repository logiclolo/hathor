# $Id: Makefile 110756 2012-04-25 02:10:32Z klaymen $
export HATHOR=$(shell pwd)

# A literal space.
space :=
space +=

sep := _WTF_SEPARATOR_

ifeq "$(HATHORDEBUG)" "1"
a		   := @sh -x$(space)
else
a		   := @
endif

# Concatenate string $(a) and $(1)
SHELLCMD = $(subst $(sep),$(a),$(sep)$(1))

all:
	@make help

history: _doctor_check_config
	$(call SHELLCMD,bin/gen_history)

# ordinary firmware release flow
firmware: _doctor_check_config _tag _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
firmware-skip-kernel: _doctor_check_config _tag _build_firmware _prepare _firmware_check history _firmware_prerelease
release: _doctor_check_config _upload

# sample firmwar release flow
sample: _doctor_check_config _tag_sample _build_kernel _build_firmware _prepare _firmware_check history _firmware_prerelease
sample-skip-kernel: _doctor_check_config _tag_sample _build_firmware _prepare _firmware_check history _firmware_prerelease
release-sample: _doctor_check_config _upload_sample

report:
	$(call SHELLCMD,bin/bug_report_improve.py)

doctor:
	$(call SHELLCMD,bin/doctor)

doctor-again:
	$(call SHELLCMD,bin/doctor -f)

clean:
	@rm -rf output/${PRODUCTVER}

cleanall: clean
	@rm -rf release/${PRODUCTVER}

help:
	@bin/help


include lib/actions.mk

.PHONY: all history firmware release clean help
