
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

        self.res = process_all(context)
        # read in stored correct answer

        pass

    def output(self, context):
        import json
        dump = json.dumps(self.res, indent=1)

        do = DataObject("metadata.json")
        do.setContent(dump)

        self.fsys.create_local_filesystem('output')

        self.create('output', do)


def process_all(context):

    fsys = get_filesys(context)
    logger.debug("fsys= %s" % fsys)

    import os
    metadata_set = {}
    for fname in fsys.get_local_subdirectories('vasp'):
        full_fname = os.path.join(dirpath, fname)
        #logger.debug("full_fname=%s" % full_fname)
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


                # if meta:
                #     curr = metadata_set[key]
                #     curr.append(meta)
                #     metadata_set[key] = curr
                #metadata_set.update(meta)

            # if metadata_set:
            #     if "%s # %s" % schemainfo in res:
            #         curr = metadata_set["%s # %s" % schemainfo]
            #         curr.append(es["%s # %s" % schemainfo])

            #         res["%s # %s" % schemainfo] = curr
            #     else:
            #         res["%s # %s" % schemainfo]= {}
                #res.update(metadata_set)
                #res[full_fname] = metadata_set
            #print full_fname , metadata_set

    return metadata_set

