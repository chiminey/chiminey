PROC_DESTINATION='chimineywd'
INPUT_DIR='input'
OUTPUT_DIR='output'
HADOOP_INPUT='HADOOP_INPUT'
HADOOP_HOME=''

start_process_schedule:
	@sh ./start_process_schedule.sh $(PROC_DESTINATION) $(INPUT_DIR) $(OUTPUT_DIR)

process_schedule_done:
	@sh ./process_schedule_done.sh

start_running_process:
	@echo running
	@sh ./start_running_process.sh $(PROC_DESTINATION) $(INPUT_DIR) $(OUTPUT_DIR)  $(HADOOP_INPUT) $(HADOOP_HOME)

process_running_done:
	@echo checking for running
	@sh ./process_running_done.sh
