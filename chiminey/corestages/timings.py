# Copyright (C) 2014, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import os
import logging

import datetime
import json
import ast

from chiminey.runsettings import getval, SettingNotFoundException
from django.conf import settings as django_settings



logger = logging.getLogger(__name__)

def microseconds_timedelta(end_time, start_time):
    try:
        start_time_time = datetime.datetime.strptime(start_time,"%Y-%m-%d  %H:%M:%S.%f")
        end_time_time = datetime.datetime.strptime(end_time,"%Y-%m-%d  %H:%M:%S.%f")
        return end_time_time - start_time_time
    except ValueError, e:
        logger.debug(e)
        return ""

def timedelta_milliseconds(end_time, start_time):
    try:
        start_time_time = datetime.datetime.strptime(start_time,"%Y-%m-%d  %H:%M:%S.%f")
        end_time_time = datetime.datetime.strptime(end_time,"%Y-%m-%d  %H:%M:%S.%f")
        return str(end_time_time - start_time_time)[:-3]
    except ValueError, e:
        logger.debug(e)
        return ""

def seconds_timedelta(end_time, start_time):
    try:
        start_time_time =  datetime.datetime.strptime(start_time,"%Y-%m-%d  %H:%M:%S")
        end_time_time =  datetime.datetime.strptime(end_time,"%Y-%m-%d  %H:%M:%S")
        return end_time_time - start_time_time
    except ValueError, e:
        logger.debug(e)
        return ""

def timedelta_seconds(end_time, start_time):
    try:
        start_time_time =  datetime.datetime.strptime(start_time,"%Y-%m-%d  %H:%M:%S")
        end_time_time =  datetime.datetime.strptime(end_time,"%Y-%m-%d  %H:%M:%S")
        return str(end_time_time - start_time_time)
    except ValueError, e:
        logger.debug(e)
        return ""

def to_string_seconds(timedelta_t):
    return str(timedelta_t)

def to_string_milliseconds(timedelta_t):
    return str(timedelta_t)[:-3]

def datetime_now_milliseconds():
    #return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def datetime_now_seconds():
    #return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def timedelta_initiate():
    return datetime.timedelta(0)
    
def to_timedelta_microseconds(timestring):
    timedata = datetime.datetime.strptime(timestring,"%H:%M:%S.%f")
    return datetime.timedelta(hours=timedata.hour, minutes=timedata.minute, seconds=timedata.second, microseconds=timedata.microsecond)

def to_timedelta_seconds(timestring):
    timedata = datetime.datetime.strptime(timestring,"%H:%M:%S")
    return datetime.timedelta(hours=timedata.hour, minutes=timedata.minute, seconds=timedata.second)

def get_datetime_value(run_settings, key):
    try:
        return str(getval(run_settings, key % django_settings.SCHEMA_PREFIX))
    except SettingNotFoundException, e:
        logger.debug(e)
        raise 
    except ValueError, e:
        logger.warn(e)
        raise

def find_min(timedata):
    pass
    
def analyse_timings_data(run_settings):
    job_id = str(getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX))
    timings_dir = os.path.join(django_settings.STATIC_ROOT,'dumps',job_id)
    timings_file = os.path.join(timings_dir,'current_processes.txt')
    timings_file_copy = os.path.join(timings_dir,'current_processes_copy.txt')
    process_report = os.path.join(timings_dir,'process_report.txt')
    stage_report = os.path.join(timings_dir,'stage_report.txt')
    #report_file=os.path.join(timings_dir,'current_processes.txt')
   
    process_timings_list = []
    process_timings_report = [ 
                      {
                       "schedule_total_time": "",
                       "schedule_minimum_time": "",
                       "schedule_maximum_time": "",
                       "schedule_average_time": "",
                      }, 
                      {
                       "variation_input_transfer_total_time": "",
                       "variation_input_transfer_minimum_time": "",
                       "variation_input_transfer_maximum_time": "",
                       "variation_input_transfer_average_time": "",
                      }, 
                      {
                       "execute_total_time": "",
                       "execute_minimum_time": "",
                       "execute_maximum_time": "",
                       "execute_average_time": "",
                      }, 
                      {
                       "output_transfer_total_time": "",
                       "output_transfer_minimum_time": "",
                       "output_transfer_maximum_time": "",
                       "output_transfer_average_time": "",
                      }, 
                     ]
    stage_timings_report = [
                            {
                             "1.schedule_stage_start_time" :  
                             str(getval (run_settings, '%s/stages/schedule/schedule_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "2.schedule_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/schedule/schedule_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "3.schedule_stage_total_time" : 
                             str(getval (run_settings, '%s/stages/schedule/schedule_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                            {
                             "1.execute_stage_start_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "2.variation_input_transfer_start_time" : 
                             str(getval (run_settings, '%s/stages/execute/variation_input_transfer_start_time' % django_settings.SCHEMA_PREFIX)),
                             "3.variation_input_transfer_end_time" : 
                             str(getval (run_settings, '%s/stages/execute/variation_input_transfer_end_time' % django_settings.SCHEMA_PREFIX)),
                             "4.execute_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "5.variation_input_transfer_total_time" : 
                             str(getval (run_settings, '%s/stages/execute/total_variation_input_transfer_time' % django_settings.SCHEMA_PREFIX)),
                             "6.execute_stage_total_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                            {
                             "1.wait_stage_start_time" :
                             str(getval (run_settings, '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "2.output_transfer_start_time" :
                             str(getval (run_settings, '%s/stages/wait/output_transfer_start_time' % django_settings.SCHEMA_PREFIX)),
                             "3.output_transfer_end_time" : 
                             str(getval (run_settings, '%s/stages/wait/output_transfer_end_time' % django_settings.SCHEMA_PREFIX)),
                             "4.wait_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/wait/wait_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "5.output_transfer_total_time" : 
                             str(getval (run_settings, '%s/stages/wait/output_transfer_total_time' % django_settings.SCHEMA_PREFIX)),
                             "6.wait_stage_total_time" :
                             str(getval (run_settings, '%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                            {
                             "1.converge_stage_start_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "2.converge_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "3.converge_stage_total_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                           ]

    if os.path.exists(timings_dir):
        if os.path.exists(timings_file):
            with open(timings_file) as json_data: 
                process_timings_list =  json.load(json_data)

    if process_timings_list:

       sched_total_time = datetime.timedelta(0)
       sched_max_time = sched_min_time = to_timedelta_microseconds(process_timings_list[0]['sched_total_time'])

       varinp_transfer_total_time = datetime.timedelta(0)
       varinp_transfer_max_time =  varinp_transfer_min_time = to_timedelta_microseconds(process_timings_list[0]['varinp_transfer_total_time'])

       exec_total_time = datetime.timedelta(0)
       exec_max_time = exec_min_time = to_timedelta_microseconds(process_timings_list[0]['exec_total_time'])

       output_transfer_total_time = datetime.timedelta(0)
       output_transfer_max_time = output_transfer_min_time = to_timedelta_microseconds(process_timings_list[0]['output_transfer_total_time'])

       for json_obj in process_timings_list:

           sched_total_time_current = to_timedelta_microseconds(json_obj['sched_total_time'])
           sched_total_time = sched_total_time + sched_total_time_current
           if sched_total_time_current < sched_min_time:
               sched_min_time = sched_total_time_current
           if sched_total_time_current > sched_min_time:
               sched_max_time = sched_total_time_current

           varinp_transfer_total_time_current = to_timedelta_microseconds(json_obj['varinp_transfer_total_time'])
           varinp_transfer_total_time = varinp_transfer_total_time + varinp_transfer_total_time_current
           if varinp_transfer_total_time_current < varinp_transfer_min_time:
               varinp_transfer_min_time = varinp_transfer_total_time_current
           if varinp_transfer_total_time_current > varinp_transfer_min_time:
               varinp_transfer_max_time = varinp_transfer_total_time_current

           exec_total_time_current = to_timedelta_microseconds(json_obj['exec_total_time'])
           exec_total_time = exec_total_time + exec_total_time_current
           if exec_total_time_current < exec_min_time:
               exec_min_time = exec_total_time_current
           if exec_total_time_current > exec_min_time:
               exec_max_time = exec_total_time_current

           output_transfer_total_time_current = to_timedelta_microseconds(json_obj['output_transfer_total_time'])
           output_transfer_total_time = output_transfer_total_time + output_transfer_total_time_current
           if output_transfer_total_time_current < output_transfer_min_time:
               output_transfer_min_time = output_transfer_total_time_current
           if output_transfer_total_time_current > output_transfer_min_time:
               output_transfer_max_time = output_transfer_total_time_current

       #process_timings_report[0]["schedule_total_time"] = str(sched_total_time)[:-3]
       process_timings_report[0]["schedule_minimum_time"] = str(sched_min_time)[:-3]
       process_timings_report[0]["schedule_maximum_time"] = str(sched_max_time)[:-3]
       process_timings_report[0]["schedule_average_time"] = str(sched_total_time / len(process_timings_list))[:-3]

       #process_timings_report[1]["variation_input_transfer_total_time"] = str(varinp_transfer_total_time)[:-3]
       process_timings_report[1]["variation_input_transfer_minimum_time"] = str(varinp_transfer_min_time)[:-3]
       process_timings_report[1]["variation_input_transfer_maximum_time"] = str(varinp_transfer_max_time)[:-3]
       process_timings_report[1]["variation_input_transfer_average_time"] = str(varinp_transfer_total_time / len(process_timings_list))[:-3]

       #process_timings_report[2]["execute_total_time"] = str(exec_total_time)[:-3]
       process_timings_report[2]["execute_minimum_time"] = str(exec_min_time)[:-3]
       process_timings_report[2]["execute_maximum_time"] = str(exec_max_time)[:-3]
       process_timings_report[2]["execute_average_time"] = str(exec_total_time / len(process_timings_list))[:-3]

       #process_timings_report[3]["output_transfer_total_time"] = str(output_transfer_total_time)[:-3]
       process_timings_report[3]["output_transfer_minimum_time"] = str(output_transfer_min_time)[:-3]
       process_timings_report[3]["output_transfer_maximum_time"] = str(output_transfer_max_time)[:-3]
       process_timings_report[3]["output_transfer_average_time"] = str(output_transfer_total_time / len(process_timings_list))[:-3]

       with open(timings_file, 'a') as fh:
           fh.write("\n" + "="*30 + "\n" + "Process Level Timings Report" + "\n" + "-"*30 + "\n")
           json.dump(process_timings_report, fh, indent=4, sort_keys=True, ensure_ascii = False)
           fh.write("\n" + "="*30 + "\n" + "Stage Level Timings Report" + "\n" + "-"*30 + "\n")
           json.dump(stage_timings_report, fh, indent=4, sort_keys=True, ensure_ascii = False)

       with open(timings_file_copy, 'w') as fh:
           json.dump(process_timings_list, fh, indent=4, sort_keys=True, ensure_ascii = False)
       with open(process_report, 'w') as fh:
           json.dump(process_timings_report, fh, indent=4, sort_keys=True, ensure_ascii = False)
       with open(stage_report, 'w') as fh:
           json.dump(stage_timings_report, fh, indent=4, sort_keys=True, ensure_ascii = False)


def create_timings_dump(job_id, file_name):
    dumps_dir= os.path.join(django_settings.STATIC_ROOT,'dumps',job_id)
    dump_file=os.path.join(dumps_dir,file_name + '.txt')
    dump_ref=os.path.join('dumps',job_id,file_name + '.txt')
    if not os.path.exists(dumps_dir):
        os.makedirs(dumps_dir)
    open(dump_file, 'w').close()
    return dump_file
               
def update_timings_dump(file_name, json_data):
    with open(file_name, 'a') as fh:
        json.dump(json_data, fh, indent=4, sort_keys=True, ensure_ascii = False)
