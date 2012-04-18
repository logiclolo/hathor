
export HATHOR=.

all:

tag:

history: 
	@bin/gen_history

upload: history
	@bin/rt_ticket_send

clean:
	@rm -f output/*

help:
	@

.PHONY: history upload clean tag all
