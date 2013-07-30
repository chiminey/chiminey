PSD_PACKAGE=PSDCode
HRMC_PACKAGE=HRMC2
PAYLOAD_NAME='process_payload
IDS='proc_ids'
# version 2.0

#deprecated
setupstart: do_setup

startsetup: do_setup

setupdone:
	@sh ./env_setupdone.sh

do_setup:
	@echo do_setup starting
	@sh ./env_setupstart.sh >& setup.output &

schedulestart:
	@sh ./schedule_start $(PAYLOAD_NAME) $(IDS)

scheduledone:
	@sh ./schedule_done $(IDS)

startrun:
	@sh ./start_run $(IDS)

running:
	@echo checking for running
	@sh ./running.sh

