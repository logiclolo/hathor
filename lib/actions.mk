_tag: 
	@bin/firmware_tag_create

_build_kernel:
	@bin/firmware_build kernel

_build_firmware:
	@bin/firmware_build firmware

_firmware_check:
	@bin/firmware_compare

_firmware_prerelease: 
	@bin/firmware_prerelease

_upload:
	@bin/merge_history
	@bin/firmware_copy
	@bin/rt_ticket_send

_prepare:
	@bin/prepare_config_generation

.PHONY: _tag _build_kernel _build_firmware _firmware_check _firmware_prerelease _upload
