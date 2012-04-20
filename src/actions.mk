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

.PHONY: _tag _build_kernel _build_firmware _firmware_check _firmware_release _upload