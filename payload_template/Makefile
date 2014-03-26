# This Makefile provides an  API through which the Chiminey server
# sets-up execution environment, executes domain-specific programs and
# monitor setup and execution progress. Therefore, the contents of the
# Makesfiles should not be changed, else Chiminey will be unable to
# drive the payload.

PAYLOAD_NAME='process_payload'
IDS='proc_ids'

# start execution of the bootstrapping procedure
start_bootstrap:
	@echo bootstrap starting
	@sh ./start_bootstrap.sh >& bootstrap.output &

# indicate whether bootstrapping procedure is finished
bootstrap_done:
	@sh ./bootstrap_done.sh

# start execution of the scheduling procedure
start_schedule:
	@sh ./start_schedule.sh $(PAYLOAD_NAME) $(IDS)

# indicate wthether scheduling procedure has finished
schedule_done:
	@sh ./schedule_done.sh $(IDS)