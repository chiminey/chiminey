from django.template import Context, Template
from django.template import TemplateSyntaxError
from django.conf import settings as django_settings
import sys
import os
import re
import json
import logging
from pprint import pformat
from django.conf import settings
settings.configure()

logger = logging.getLogger(__name__)

def get_content(iid,fn):
        input_fname = os.path.join(iid, fn)
        template_content = ''
        with open(input_fname) as file:
            template_content = file.read()
        print template_content
        return template_content

def write_content(fname,content):
        with open(fname, "w") as fh: 
            fh.write(content) 

def start_variation(node_settings):
        template_pat = re.compile("(.*)_template")
        for context in node_settings['context_list']:
            logger.debug("local_context=%s" % context)

            initial_input_dir = os.path.join(os.environ['HOME'], node_settings['initial_input_dir'], 'initial')
            input_files = os.listdir(initial_input_dir)
            print input_files

            # get process information
            run_counter = context['run_counter']
            logger.debug("run_counter=%s" % run_counter)
            proc = None
            for p in node_settings['processes']:
                # TODO: how to handle invalid run_counter
                pid = int(p['id'])
                logger.debug("pid=%s" % pid)
                if pid == run_counter:
                    proc = p
                    break
            else:
                logger.error("no process found matching run_counter")
                raise BadInputException()
            logger.debug("proc=%s" % pformat(proc))

            schedule_procs = node_settings['schedule_processes']
            #for iterator, p in enumerate(schedule_procs):
            #   if int(p['id']) == int(proc['id']):
            #       schedule_procs[iterator]['varinp_transfer_start_time'] = timings.datetime_now_milliseconds()


            for fname in input_files:
                logger.debug("fname=%s" % fname)
                templ_mat = template_pat.match(fname)

                outputs = []
                if templ_mat:
                    base_fname = templ_mat.group(1)
                    template_content = get_content(initial_input_dir, fname) 
                    print template_content
                    try:
                        templ = Template(template_content)
                    except TemplateSyntaxError, e:
                        logger.error(e)
                        # FIXME: should detect this during submission of job,
                        # as no sensible way to recover here.
                        # TODO: signal error conditions in job status
                        continue
                    new_context = Context(context)
                    logger.debug("new_content=%s" % new_context)
                    render_output = templ.render(new_context)
                    render_output = render_output.encode('utf-8')
                    outputs.append((base_fname, render_output))
                    outputs.append((fname, template_content))

                else:
                    content = get_content(initial_input_dir, fname) 
                    outputs.append((fname, content))

                for (new_fname, content) in outputs:
                    dest_file_location = os.path.join(os.environ['PWD'], proc['id'], 'smart_connector_input', new_fname)
                    logger.debug("dest_file_location =%s" % dest_file_location)
                    print dest_file_location
                    write_content(dest_file_location, content)


            logger.debug("writing values file")
            values_dest_location = os.path.join(os.environ['PWD'], proc['id'], 'smart_connector_input','values')
            write_content(values_dest_location, json.dumps(context, indent=4))

        logger.debug("done input upload")

def main():
    settings = {}
    with open(sys.argv[1]) as json_data:
        settings = json.load(json_data)

    print settings
    #print settings['context_list']
    
    start_variation(settings)    

if __name__== "__main__":
  main()
