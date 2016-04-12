RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

start_process_schedule:
	@sh ./start_process_schedule.sh $(RUN_ARGS)

process_schedule_done:
	@sh ./process_schedule_done.sh

start_running_process:
	@echo running
	@sh ./start_running_process.sh  $(RUN_ARGS)

process_running_done:
	@echo checking for running
	@sh ./process_running_done.sh