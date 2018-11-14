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
import csv

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
        #time_delta = end_time_time - start_time_time
        #return str(time_delta)[:-3], time_delta.total_seconds()
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
        time_delta = end_time_time - start_time_time
        return str(end_time_time - start_time_time)
#        time_delta = end_time_time - start_time_time
#        return str(time_delta), time_delta.total_seconds()
    except ValueError, e:
        logger.debug(e)
        return ""

def to_string_seconds(timedelta_t):
    return str(timedelta_t)

def to_string_milliseconds(timedelta_t):
    return str(timedelta_t)[:-3]

def to_string_microseconds(timedelta_t):
    return str(timedelta_t)

def datetime_now_milliseconds():
    #return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def datetime_now_seconds():
    #return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def timedelta_initiate():
    return datetime.timedelta(0)
    
def to_timedelta_microseconds(timestring):
    tdelta = datetime.timedelta(0)
    try:
        timedata = datetime.datetime.strptime(timestring,"%H:%M:%S.%f")
        tdelta = datetime.timedelta(hours=timedata.hour, minutes=timedata.minute, seconds=timedata.second, microseconds=timedata.microsecond)
    except ValueError, e:
        logger.debug(e)
    return tdelta

def to_timedelta_seconds(timestring):
    tdelta = datetime.timedelta(0)
    try:
        timedata = datetime.datetime.strptime(timestring,"%H:%M:%S")
        tdelta = datetime.timedelta(hours=timedata.hour, minutes=timedata.minute, seconds=timedata.second)
    except ValueError, e:
        logger.debug(e)
    return tdelta

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

def report_stage_timings(timings_file, stage_csv_file, run_settings):

    job_id = str(getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX))
    directive_name = str(getval(run_settings, '%s/directive_profile/directive_name' % django_settings.SCHEMA_PREFIX))
    number_vm_instances = str(getval(run_settings, '%s/input/system/compplatform/cloud/number_vm_instances' % django_settings.SCHEMA_PREFIX))
    total_processes = str(getval(run_settings, '%s/stages/schedule/total_processes' % django_settings.SCHEMA_PREFIX))

    schedule_stage_total_time =  str(getval (run_settings, '%s/stages/schedule/schedule_stage_total_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('schedule_stage_total_time=%s' % schedule_stage_total_time)
    schedule_stage_total_time =  to_timedelta_seconds(schedule_stage_total_time).total_seconds()

    variation_input_transfer_total_time = str(getval (run_settings, '%s/stages/execute/total_variation_input_transfer_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('variation_input_transfer_total_time=%s' % variation_input_transfer_total_time)
    variation_input_transfer_total_time = to_timedelta_seconds(variation_input_transfer_total_time).total_seconds()

    execute_stage_total_time =  str(getval (run_settings, '%s/stages/execute/execute_stage_total_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('execute_stage_total_time=%s' % execute_stage_total_time)
    execute_stage_total_time =  to_timedelta_seconds(execute_stage_total_time).total_seconds()


    output_transfer_total_time = str(getval (run_settings, '%s/stages/wait/output_transfer_total_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('output_transfer_total_time=%s' % output_transfer_total_time)
    output_transfer_total_time = to_timedelta_seconds(output_transfer_total_time).total_seconds()

    wait_stage_total_time = str(getval (run_settings, '%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('wait_stage_total_time=%s' % wait_stage_total_time)
    wait_stage_total_time = to_timedelta_seconds(wait_stage_total_time).total_seconds()

    converge_stage_total_time = str(getval (run_settings, '%s/stages/converge/converge_stage_total_time' % django_settings.SCHEMA_PREFIX))
    logger.debug('converge_stage_total_time=%s' % converge_stage_total_time)
    converge_stage_total_time = to_timedelta_seconds(converge_stage_total_time).total_seconds()

    execute_total_time = wait_stage_total_time - output_transfer_total_time
    total_processing_time = schedule_stage_total_time +  execute_stage_total_time  + wait_stage_total_time + converge_stage_total_time

    stage_timings_csv_report = [ 
                      {
                       "schedule_stage_total_time" : str(schedule_stage_total_time),
                       "variation_input_transfer_total_time" : str (variation_input_transfer_total_time), 
                       "execute_stage_total_time" : str(execute_stage_total_time),
                       "output_transfer_total_time" : str(output_transfer_total_time),
                       "wait_stage_total_time" : str(wait_stage_total_time),
                       "execute_total_time" : str(execute_total_time),
                       "converge_stage_total_time" : str(converge_stage_total_time),
                       "total_processing_time" : str(total_processing_time),
                       "job_id" : job_id,
                       "number_vm_instances" : number_vm_instances,
                       "directive_name" : directive_name,
                       "total_processes" : total_processes
                      } 
                     ]

    stage_timings_report = [
                            {
                             "schedule_stage_start_time" :  
                             str(getval (run_settings, '%s/stages/schedule/schedule_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "schedule_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/schedule/schedule_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "schedule_stage_total_time" : schedule_stage_total_time
                            },
                            {
                             "execute_stage_start_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "variation_input_transfer_start_time" : 
                             str(getval (run_settings, '%s/stages/execute/variation_input_transfer_start_time' % django_settings.SCHEMA_PREFIX)),
                             "variation_input_transfer_end_time" : 
                             str(getval (run_settings, '%s/stages/execute/variation_input_transfer_end_time' % django_settings.SCHEMA_PREFIX)),
                             "execute_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "variation_input_transfer_total_time" : 
                             str(getval (run_settings, '%s/stages/execute/total_variation_input_transfer_time' % django_settings.SCHEMA_PREFIX)),
                             "execute_stage_total_time" : 
                             str(getval (run_settings, '%s/stages/execute/execute_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                            {
                             "wait_stage_start_time" :
                             str(getval (run_settings, '%s/stages/wait/wait_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "output_transfer_start_time" :
                             str(getval (run_settings, '%s/stages/wait/output_transfer_start_time' % django_settings.SCHEMA_PREFIX)),
                             "output_transfer_end_time" : 
                             str(getval (run_settings, '%s/stages/wait/output_transfer_end_time' % django_settings.SCHEMA_PREFIX)),
                             "wait_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/wait/wait_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "output_transfer_total_time" : 
                             str(getval (run_settings, '%s/stages/wait/output_transfer_total_time' % django_settings.SCHEMA_PREFIX)),
                             "wait_stage_total_time" :
                             str(getval (run_settings, '%s/stages/wait/wait_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                            {
                             "converge_stage_start_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_start_time' % django_settings.SCHEMA_PREFIX)),
                             "converge_stage_end_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_end_time' % django_settings.SCHEMA_PREFIX)),
                             "converge_stage_total_time" : 
                             str(getval (run_settings, '%s/stages/converge/converge_stage_total_time' % django_settings.SCHEMA_PREFIX)),
                            },
                           ]
    write_json_report(timings_file, stage_timings_report, "Stage Level Timings Report")

    write_csv_dictlist(stage_csv_file, stage_timings_csv_report) 

    #write_csv_dictlist(stage_csv_file, merge_dictionary(stage_timings_report)) 

    return stage_timings_report

def report_process_timings(timings_file, timings_csv_file, process_csv_file, run_settings):
   
    job_id = str(getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX))
    directive_name = str(getval(run_settings, '%s/directive_profile/directive_name' % django_settings.SCHEMA_PREFIX))
    number_vm_instances = str(getval(run_settings, '%s/input/system/compplatform/cloud/number_vm_instances' % django_settings.SCHEMA_PREFIX))
    total_processes = str(getval(run_settings, '%s/stages/schedule/total_processes' % django_settings.SCHEMA_PREFIX))


    process_timings_report = [ 
                      {
                       "schedule_minimum_time": "",
                       "schedule_maximum_time": "",
                       "schedule_average_time": "",
                      }, 
                      {
                       "variation_input_transfer_minimum_time": "",
                       "variation_input_transfer_maximum_time": "",
                       "variation_input_transfer_average_time": "",
                      }, 
                      {
                       "execute_minimum_time": "",
                       "execute_maximum_time": "",
                       "execute_average_time": "",
                      }, 
                      {
                       "output_transfer_minimum_time": "",
                       "output_transfer_maximum_time": "",
                       "output_transfer_average_time": "",
                      }, 
                     ]

    process_timings_csv_report = [ 
                      {
                       "schedule_minimum_time": "",
                       "schedule_maximum_time": "",
                       "schedule_average_time": "",
                       "variation_input_transfer_minimum_time": "",
                       "variation_input_transfer_maximum_time": "",
                       "variation_input_transfer_average_time": "",
                       "execute_minimum_time": "",
                       "execute_maximum_time": "",
                       "execute_average_time": "",
                       "output_transfer_minimum_time": "",
                       "output_transfer_maximum_time": "",
                       "output_transfer_average_time": "",
                       "job_id" : job_id,
                       "number_vm_instances" : number_vm_instances,
                       "directive_name" : directive_name,
                       "total_processes" : total_processes
                      } 
                     ]

    process_timings_list = read_json_file(timings_file) 

    if process_timings_list:
       sched_total_time = datetime.timedelta(0)
       sched_max_time = sched_min_time = to_timedelta_microseconds(process_timings_list[0]['sched_total_time'])
       #sched_max_time = sched_min_time = process_timings_list[0]['sched_total_time']

       varinp_transfer_total_time = datetime.timedelta(0)
       varinp_transfer_max_time =  varinp_transfer_min_time = to_timedelta_microseconds(process_timings_list[0]['varinp_transfer_total_time'])
       #varinp_transfer_max_time =  varinp_transfer_min_time = process_timings_list[0]['varinp_transfer_total_time']

       exec_total_time = datetime.timedelta(0)
       exec_max_time = exec_min_time = to_timedelta_microseconds(process_timings_list[0]['exec_total_time'])
       #exec_max_time = exec_min_time = process_timings_list[0]['exec_total_time']

       output_transfer_total_time = datetime.timedelta(0)
       output_transfer_max_time = output_transfer_min_time = to_timedelta_microseconds(process_timings_list[0]['output_transfer_total_time'])
       #output_transfer_max_time = output_transfer_min_time = process_timings_list[0]['output_transfer_total_time']

       for json_obj in process_timings_list:

           sched_total_time_current = to_timedelta_microseconds(json_obj['sched_total_time'])
           #sched_total_time_current = json_obj['sched_total_time']
           sched_total_time = sched_total_time + sched_total_time_current
           if sched_total_time_current < sched_min_time:
               sched_min_time = sched_total_time_current
           if sched_total_time_current > sched_min_time:
               sched_max_time = sched_total_time_current

           varinp_transfer_total_time_current = to_timedelta_microseconds(json_obj['varinp_transfer_total_time'])
           #varinp_transfer_total_time_current = json_obj['varinp_transfer_total_time']
           varinp_transfer_total_time = varinp_transfer_total_time + varinp_transfer_total_time_current
           if varinp_transfer_total_time_current < varinp_transfer_min_time:
               varinp_transfer_min_time = varinp_transfer_total_time_current
           if varinp_transfer_total_time_current > varinp_transfer_min_time:
               varinp_transfer_max_time = varinp_transfer_total_time_current

           exec_total_time_current = to_timedelta_microseconds(json_obj['exec_total_time'])
           #exec_total_time_current = json_obj['exec_total_time']
           exec_total_time = exec_total_time + exec_total_time_current
           if exec_total_time_current < exec_min_time:
               exec_min_time = exec_total_time_current
           if exec_total_time_current > exec_min_time:
               exec_max_time = exec_total_time_current

           output_transfer_total_time_current = to_timedelta_microseconds(json_obj['output_transfer_total_time'])
           #output_transfer_total_time_current = json_obj['output_transfer_total_time']
           output_transfer_total_time = output_transfer_total_time + output_transfer_total_time_current
           if output_transfer_total_time_current < output_transfer_min_time:
               output_transfer_min_time = output_transfer_total_time_current
           if output_transfer_total_time_current > output_transfer_min_time:
               output_transfer_max_time = output_transfer_total_time_current
      
       total_json_obj = len(process_timings_list)
       #process_timings_report[0]["schedule_total_time"] = str(sched_total_time)[:-3]
       process_timings_report[0]["schedule_minimum_time"] = str(sched_min_time)[:-3]
       process_timings_report[0]["schedule_maximum_time"] = str(sched_max_time)[:-3]
       process_timings_report[0]["schedule_average_time"] = str(sched_total_time / total_json_obj)[:-3]
       process_timings_csv_report[0]["schedule_minimum_time"] = str(sched_min_time.total_seconds())
       process_timings_csv_report[0]["schedule_maximum_time"] = str(sched_max_time.total_seconds())
       process_timings_csv_report[0]["schedule_average_time"] = str(round((sched_total_time.total_seconds() / total_json_obj),3))

       #process_timings_report[1]["variation_input_transfer_total_time"] = str(varinp_transfer_total_time)[:-3]
       process_timings_report[1]["variation_input_transfer_minimum_time"] = str(varinp_transfer_min_time)[:-3]
       process_timings_report[1]["variation_input_transfer_maximum_time"] = str(varinp_transfer_max_time)[:-3]
       process_timings_report[1]["variation_input_transfer_average_time"] = str(varinp_transfer_total_time / total_json_obj)[:-3]
       process_timings_csv_report[0]["variation_input_transfer_minimum_time"] = str(varinp_transfer_min_time.total_seconds())
       process_timings_csv_report[0]["variation_input_transfer_maximum_time"] = str(varinp_transfer_max_time.total_seconds())
       process_timings_csv_report[0]["variation_input_transfer_average_time"] = str(round((varinp_transfer_total_time.total_seconds() / total_json_obj),3))

       #process_timings_report[2]["execute_total_time"] = str(exec_total_time)[:-3]
       process_timings_report[2]["execute_minimum_time"] = str(exec_min_time)[:-3]
       process_timings_report[2]["execute_maximum_time"] = str(exec_max_time)[:-3]
       process_timings_report[2]["execute_average_time"] = str(exec_total_time / total_json_obj)[:-3]
       process_timings_csv_report[0]["execute_minimum_time"] = str(exec_min_time.total_seconds())
       process_timings_csv_report[0]["execute_maximum_time"] = str(exec_max_time.total_seconds())
       process_timings_csv_report[0]["execute_average_time"] = str(round((exec_total_time.total_seconds() / total_json_obj),3))

       #process_timings_report[3]["output_transfer_total_time"] = str(output_transfer_total_time)[:-3]
       process_timings_report[3]["output_transfer_minimum_time"] = str(output_transfer_min_time)[:-3]
       process_timings_report[3]["output_transfer_maximum_time"] = str(output_transfer_max_time)[:-3]
       process_timings_report[3]["output_transfer_average_time"] = str(output_transfer_total_time / total_json_obj)[:-3]
       process_timings_csv_report[0]["output_transfer_minimum_time"] = str(output_transfer_min_time.total_seconds())
       process_timings_csv_report[0]["output_transfer_maximum_time"] = str(output_transfer_max_time.total_seconds())
       process_timings_csv_report[0]["output_transfer_average_time"] = str(round((output_transfer_total_time.total_seconds() / total_json_obj),3))

       write_json_report(timings_file, process_timings_report, "Process Level Timings Report")
       write_csv_dictlist(process_csv_file, process_timings_csv_report) 
       write_csv_dictlist(timings_csv_file, process_timings_list) 
       #write_csv_dictlist(timings_csv_file, merge_dictionary(process_timings_list)) 


def write_json_report(timings_file, timings_data, message):
    with open(timings_file, 'a') as fh:
       fh.write("\n" + "="*30 + "\n" + message + "\n" + "-"*30 + "\n")
       json.dump(timings_data, fh, indent=4, sort_keys=True, ensure_ascii = False)
    
def analyse_timings_data(run_settings):
    job_id = str(getval(run_settings, '%s/system/contextid' % django_settings.SCHEMA_PREFIX))
    dumps_dir = os.path.join(django_settings.STATIC_ROOT,'dumps')
    timings_dir = os.path.join(dumps_dir,job_id)
    timings_file = os.path.join(timings_dir,'current_processes.txt')
    timings_csv_file = os.path.join(timings_dir,'current_processes.csv')
    process_csv_file = os.path.join(dumps_dir,'process_report.csv')
    stage_csv_file = os.path.join(dumps_dir,'stage_report.csv')

    report_process_timings(timings_file, timings_csv_file, process_csv_file, run_settings) 
    report_stage_timings(timings_file, stage_csv_file, run_settings)


def dictwrite_csv_dictlist(filename, data):
    file_exists = False
    if os.path.exists(filename):
       file_exists = True
    i = 0
    for dict_obj in data:
        with open( filename , 'ab') as fh: 
            w = csv.DictWriter(fh, data[i].keys())
            if not file_exists and i == 0:
                w.writeheader()
            w.writerow(data[i])
        i+=1

def dictwrite_csv_dict(filename, data):
    file_exists = False
    if os.path.exists(filename):
       file_exists = True
    with open( filename , 'ab') as fh: 
        w = csv.DictWriter(fh, data.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(data)

def read_json_file(timings_file):
    process_timings_report = []
    if os.path.exists(timings_file):
        with open(timings_file, "r") as json_data:
            process_timings_report =  json.load(json_data)
    return process_timings_report

def write_csv_dictlist(filename, json_data):
    with open(filename, 'ab') as csvfh:
        writer = csv.writer(csvfh)
        headers = []
        for key in sorted(json_data[0]):
            headers.append(key)
        if csvfh.tell() == 0:
            writer.writerow(headers)
        for row in json_data:
            targetrow = []
            for key in headers:
                targetrow.append(row[key])
            writer.writerow(targetrow)

def merge_dictionary(json_data):
    one_dict = {}
    dict_list = []
    for dict_item in json_data:
        one_dict.update(dict_item)
    dict_list.append(one_dict)
    return dict_list


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

def create_log_file(job_id, file_name):
    dumps_dir= os.path.join(django_settings.STATIC_ROOT,'dumps',job_id)
    dump_file=os.path.join(dumps_dir,file_name)
    dump_ref=os.path.join('dumps',job_id,file_name)
    if not os.path.exists(dumps_dir):
        os.makedirs(dumps_dir)
    open(dump_file, 'w').close()
    return dump_file

def update_log_file(filename, text):
    with open(filename, "a") as logf:
        logf.write(text)

def create_input_output_log(job_id, file_name):
    dumps_dir= os.path.join(django_settings.STATIC_ROOT,'dumps',job_id)
    dump_file=os.path.join(dumps_dir,file_name)
    dump_ref=os.path.join('dumps',job_id,file_name)
    if not os.path.exists(dumps_dir):
        os.makedirs(dumps_dir)
    open(dump_file, 'w').close()
    return dump_file

