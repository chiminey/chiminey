RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

start_process_schedule:
	@bash ./start_process_schedule.sh $(RUN_ARGS)

process_schedule_done:
	@bash ./process_schedule_done.sh

start_processing:
	@bash ./start_processing.sh $(RUN_ARGS) >& start_processing.output &

start_running_process:
	@echo running
	@bash ./start_running_process.sh  $(RUN_ARGS) 

process_running_done:
	@echo checking for running
	@bash ./process_running_done.sh
