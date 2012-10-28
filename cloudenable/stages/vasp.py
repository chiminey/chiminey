# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the RMIT, the RMIT members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import logging
import logging.config

from metadata import rulesets
from metadata import process_datafile
from filesystem import DataObject
from filesystem import FileSystem
from hrmcstages import get_filesys
from smartconnector import Stage

logger = logging.getLogger('stages')

class VASP(Stage):
    """ 
    Given a filesystem vasp contining VASP files, extracts metadata and stores in 
    output/metadata.json 
    """
    def __init__(self):
        pass

    def triggered(self, context):

        self.fs = get_filesys(context)
        logger.debug("fsys= %s" % self.fs)
        local_file = self.fs.local_filesystem_exists('vasp')
        if local_file:
            return not self.fs.local_filesystem_exists('output')
        return False

    def process(self, context):
        self.fsys = get_filesys(context)
        logger.debug("fsys= %s" % self.fs)
        self.res = self._process_all(context)

    def _process_all(self, context):
        fsys = get_filesys(context)
        logger.debug("fsys= %s" % fsys)
        import os
        metadata_set = {}
        for fname in fsys.get_local_subdirectories('vasp'):
            full_fname = os.path.join(os.path.join(fsys.global_filesystem,
                                                  'vasp', fname))
            logger.debug("full_fname=%s" % full_fname)
            for schemainfo in rulesets:
                meta = process_datafile(fname, full_fname, rulesets[schemainfo])
                key = "%s # %s" % schemainfo
                print "meta=%s" % meta
                if key in metadata_set:
                    curr = metadata_set[key]
                    logger.debug("curr=%s" % curr)
                    curr.update(meta)
                    logger.debug("curr=%s" % curr)
                    if curr:
                        metadata_set[key] = curr
                else:
                    if meta:
                        metadata_set[key] = meta

        return metadata_set

    def output(self, context):
        import json
        dump = json.dumps(self.res, indent=1)
        do = DataObject("metadata.json")
        do.setContent(dump)
        self.fsys.create_local_filesystem('output')
        self.fsys.create('output', do)

