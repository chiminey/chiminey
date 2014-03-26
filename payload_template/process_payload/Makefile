# This Makefile provides an API through which the Chiminey server
# sets-up execution environment, executes domain-specific programs and
# monitor setup and execution progress. Therefore, the contents of the
# Makesfiles should not be changed, else Chiminey will be unable to
# drive the payload.

# start execution of the schedule process
start_process_schedule:
	@sh ./start_process_schedule.sh

# indicate whether schedule process is finished.
process_schedule_done:
	@sh ./process_schedule_done.sh

# start execution of domain-specific code
start_running_process:
	@echo running
	@sh ./start_running_process.sh

# indicates whether domain-specific code has finished.
process_running_done:
	@echo checking for running
	@sh ./process_running_done.sh
