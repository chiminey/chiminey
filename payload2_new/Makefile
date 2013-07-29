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

startrun: psd_run_setup run_hrmc

run_hrmc:
	@echo running hrmc
	@cd $(HRMC_PACKAGE) ; ./HRMC >& output &  echo "$$!" > "run.pid"

psd_run_setup:
	echo setting up psd
	rm -f $(PSD_PACKAGE)/run.pid

running:
	@echo checking for running
	@sh ./running.sh

