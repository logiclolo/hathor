_tag: 
	@bin/firmware_tag_create

_tag_sample: 
	@bin/firmware_tag_create "sample"

_build_kernel:
	@bin/firmware_build kernel

_build_firmware:
	@bin/firmware_build firmware

_firmware_check:
	@bin/firmware_compare

_firmware_prerelease: 
	@bin/firmware_prerelease
	@echo "編譯成功! 請記得檢查做出來的 firmware 是否與原本的 firmware 相同"

_upload:
	@bin/merge_history
	@bin/firmware_copy
	# @bin/rt_ticket_send
	@bin/redmine_issue_create

_upload_sample:
	@bin/merge_history
	@bin/firmware_copy

_prepare:
	@bin/prepare_config_generation

_check_healthiness:
	@bin/check_healthiness

debug_release: 
	@bin/merge_history
	@bin/firmware_copy
	@bin/rt_ticket_send "test"

_doctor_check_config:
	@bin/doctor_check_config



.PHONY: _tag _build_kernel _build_firmware _firmware_check _firmware_prerelease _upload
