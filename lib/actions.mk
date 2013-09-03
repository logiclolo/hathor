_tag:
	$(call SHELLCMD,bin/firmware_tag_create)

_tag_sample:
	$(call SHELLCMD,bin/firmware_tag_create "sample")

_build_kernel:
	$(call SHELLCMD,bin/firmware_build kernel)

_build_firmware:
	$(call SHELLCMD,bin/firmware_build firmware)

_firmware_check:
	$(call SHELLCMD,bin/firmware_compare)

_firmware_prerelease:
	$(call SHELLCMD,bin/firmware_prerelease)
	@echo "編譯成功! 請記得檢查做出來的 firmware 是否與原本的 firmware 相同"

_upload:
	$(call SHELLCMD,bin/merge_history)
	$(call SHELLCMD,bin/firmware_copy)
	# @bin/rt_ticket_send
	$(call SHELLCMD,bin/redmine_issue_create)

_upload_sample:
	$(call SHELLCMD,bin/merge_history)
	$(call SHELLCMD,bin/firmware_copy)

_prepare:
	$(call SHELLCMD,bin/prepare_config_generation)

_check_healthiness:
	$(call SHELLCMD,bin/check_healthiness)

debug_release:
	$(call SHELLCMD,bin/merge_history)
	$(call SHELLCMD,bin/firmware_copy)
	$(call SHELLCMD,bin/rt_ticket_send "test")

_doctor_check_config:
	$(call SHELLCMD,bin/doctor_check_config)



.PHONY: _tag _build_kernel _build_firmware _firmware_check _firmware_prerelease _upload
