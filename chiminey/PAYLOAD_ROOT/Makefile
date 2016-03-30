RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)


start_bootstrap:
	@echo bootstrap starting
	@sh ./start_bootstrap.sh >& bootstrap.output &

bootstrap_done:
	@sh ./bootstrap_done.sh

start_schedule:
	@sh ./start_schedule.sh $(RUN_ARGS)

schedule_done:
	@sh ./schedule_done.sh $(IDS)