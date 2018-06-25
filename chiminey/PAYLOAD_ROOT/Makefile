RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)


start_bootstrap:
	@echo bootstrap starting
	@bash ./start_bootstrap.sh >& bootstrap.output &

bootstrap_done:
	@bash ./bootstrap_done.sh 

start_schedule:
	@bash ./start_schedule.sh $(RUN_ARGS) >& start_schedule.output &

schedule_done:
	@bash ./schedule_done.sh $(IDS) 

start_input_variation:
	@bash ./start_input_variation.sh $(RUN_ARGS) >& start_input_variation.output &
