PAYLOAD_NAME='process_payload
IDS='proc_ids'
PSD_PACKAGE=PSDCode
HRMC_PACKAGE=HRMC2
# version 2.0


schedulestart:
	@sh ./process_schedulestart.sh $(PAYLOAD_NAME) $(IDS)

scheduledone:
	@sh ./process_scheduledone.sh $(IDS)

startrun: psd_run_setup run_hrmc

run_hrmc:
	@echo running hrmc
	@sh ./start_run.sh
	@cd $(HRMC_PACKAGE) ; ./HRMC >& output &  echo "$$!" > "run.pid"

psd_run_setup:
	echo setting up psd
	rm -f $(PSD_PACKAGE)/run.pid

