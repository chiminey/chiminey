PAYLOAD_NAME='process_payload'
IDS='proc_ids'
PROC_DESTINATION='chimineywd'

start_bootstrap:
    @echo bootstrap starting
    @sh ./start_bootstrap.sh >& bootstrap.output &

bootstrap_done:
    @sh ./bootstrap_done.sh

start_schedule:
    @sh ./start_schedule.sh $(PAYLOAD_NAME) $(IDS) $(PROC_DESTINATION)

schedule_done:
    @sh ./schedule_done.sh $(IDS)