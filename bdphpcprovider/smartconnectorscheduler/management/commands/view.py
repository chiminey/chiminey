# Copyright (C) 2013, RMIT University

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


import sys
import os
import re
import json
import shutil

import logging
import logging.config

from django.core.management.base import BaseCommand, CommandError

OUTPUT_PREFIX = "output"
INPUT_PREFIX = "input"
RAW_PREFIX = "raw"


logger = logging.getLogger(__name__)

def getdirs(dir):
    return [p for p in os.listdir(dir) if os.path.isdir(os.path.join(dir,p))]


def convert_output(output_dir, view_dir, NM=8):
    os.chdir(view_dir)
    raw_dir = os.path.join(view_dir, RAW_PREFIX)

    try:
        shutil.copytree(output_dir, raw_dir)
    except os.error,e:
        print "error %s" %e

    try:
        os.makedirs(os.path.join(view_dir, INPUT_PREFIX))
    except os.error,e:
        print "error %s" %e

    try:
        os.makedirs(os.path.join(view_dir, OUTPUT_PREFIX))
    except os.error, e:
        print "error %s" % e

    trans = {}
    input_pat = re.compile("%s_([0-9]+)" % INPUT_PREFIX)
    input_dirs = [d for d in getdirs(raw_dir) if input_pat.match(d)]
    for i, indir in enumerate(input_dirs):

        input_iter_mat = input_pat.match(indir)
        if input_iter_mat:
            input_iter = input_iter_mat.group(1)
            logger.debug("input_iter=%s" % input_iter)
        else:
            logger.debug("invalid output suffix number")
            continue

        for node in getdirs(os.path.join(view_dir, RAW_PREFIX, indir)):
            rmcen_path = os.path.join(view_dir, RAW_PREFIX,  indir, node, "rmcen.inp_values")
            if os.path.exists(rmcen_path):
                logger.debug("rmcen_path=%s" % rmcen_path)
                f = open(rmcen_path, "r")  # only works for one template
                values_map = dict(json.loads(f.read()))
                if 'run_counter' in values_map:
                    run_counter = values_map['run_counter']
                    if run_counter:
                        counter_alpha = chr(ord('a') + ((run_counter % NM) -1) % NM)
                    else:
                        counter_alpha = "_"
            else:
                counter_alpha = "_"
            trans[os.path.join(indir, node)] = "%s%s" % (input_iter, counter_alpha )

    from pprint import pformat
    logger.debug("trans=%s" % pformat(trans))

    for source, dest in trans.items():
        logger.debug('view dir %s RAW_PRE %s source %s ' % (view_dir, RAW_PREFIX, source))
        os.symlink(os.path.join('..', RAW_PREFIX, source),
            os.path.join(view_dir, INPUT_PREFIX, dest))

    try:
        os.symlink(os.path.join('..', RAW_PREFIX, OUTPUT_PREFIX),
            os.path.join(OUTPUT_PREFIX, OUTPUT_PREFIX))
        #shutil.copytree(os.path.join(raw_dir,d), os.path.join(view_dir,INPUT_PREFIX,d))
    except os.error, e:
        print "error %s" % e




    output_pat = re.compile("%s_([0-9]+)" % OUTPUT_PREFIX)
    output_dirs = [d for d in getdirs(raw_dir) if output_pat.match(d)]
    trans = {}
    for i, outdir in enumerate(output_dirs):
        NM = len(getdirs(os.path.join(view_dir, RAW_PREFIX, outdir)))  # should always be same value
        logger.debug("NM = %s" % NM)
        logger.debug("#%s %s" % (i, outdir))
        output_iter_mat = output_pat.match(outdir)
        if output_iter_mat:
            output_iter = output_iter_mat.group(1)
            logger.debug("output_iter=%s" % output_iter)
        else:
            logger.debug("invalid output suffix number")
            continue

        for node in getdirs(os.path.join(view_dir, RAW_PREFIX, outdir)):
            logger.debug("node=%s" % node)
            f = open(os.path.join(view_dir, RAW_PREFIX,  outdir, node, "rmcen.inp_values"),"r")  # only works for one template
            values_map = dict(json.loads(f.read()))
            if 'generator_counter' in values_map:
                prev_numbfile = values_map['generator_counter']
                if prev_numbfile:
                    logger.debug("prev_numbfile=%s" % prev_numbfile)
                    prev_alpha = chr(ord('a') + ((prev_numbfile % NM) -1) % NM)
                else:
                    prev_alpha = "_"

            else:
                prev_alpha = ""
            logger.debug("prev_alpha=%s" % prev_alpha)

            curr_numbfile = values_map['run_counter']
            logger.debug("curr_numbfile=%s" % curr_numbfile)

#            trans[os.path.join(outdir,node)] = "%s%s%s" % (output_iter, prev_alpha, curr_numbfile % NM)
#            trans[os.path.join(outdir, node)] = "%s_%s_%s" % (output_iter, prev_numbfile, curr_numbfile )
            trans[os.path.join(outdir, node)] = "%s%s%s" % (output_iter,
                prev_alpha, ((curr_numbfile %NM) -1) % NM)

    from pprint import pformat
    logger.debug("trans=%s" % pformat(trans))
#    logger.debug("trans=%s" '\n'.join(trans.items()))

    for source, dest in trans.items():
        os.symlink(os.path.join('..', RAW_PREFIX, source),
            os.path.join(OUTPUT_PREFIX, dest))


class Command(BaseCommand):
    args = '<source dest>'
    help = 'Produces new view of output data'

    def handle(self, *args, **options):
        new_args = list(args)
        print new_args
        output_path = args[0]
        view_path = args[1]

        if os.path.exists(view_path):
            raise IOError("view path already exists. Exiting to avoid overwriting")

        os.makedirs(view_path)

        if not os.path.exists(output_path):
            raise IOError("output directory not found")
        if not os.path.isdir(output_path):
            raise IOError("output directory not found")

        convert_output(output_path, view_path)
        print "done"
