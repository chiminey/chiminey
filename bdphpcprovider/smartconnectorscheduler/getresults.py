import urllib
import urllib2
import json

import logging

logger = logging.getLogger(__name__)
import os


def get_results_fs(group_id, local_filesystem, fs):

    logger.debug("gls=%s" % fs.get_local_subdirectories(local_filesystem))
    paths = []
    for d in fs.get_local_subdirectories(local_filesystem):
        logger.debug("d=%s" % d)
        for f in fs.get_local_subdirectory_files(local_filesystem,
             d):
            logger.debug("f=%s" % f)
            paths.append(os.path.join(local_filesystem, d, f))

    logger.debug("paths=%s" % paths)

    destination = "http://127.0.0.1:8000/apps/mytardis-hpc-app" \
        + "/resultsready/%s/" % group_id
    values = {'group_id': group_id,
              'files': json.dumps(paths)}
    data = urllib.urlencode(values)
    req = urllib2.Request(destination, data,
            {'Content-Type': 'application/json'})
    response = urllib2.urlopen(req)
    the_page = response.read()

    try:
        info = json.loads(the_page)
    except ValueError as e:
        raise e

    logger.debug("info=%s" % info)
    return info
    #for filename, checksum in info.items():
    #    pass



def get_results(experiment_id, group_id, d, fs):
    """
    Send a list of output result files to mytardis_hpc_app
    """

    files = [f for f in os.listdir(d) if not os.path.isdir(d)].sorted()

    logger.debug("paths=%s" % paths)

    destination = "http://127.0.0.1:8000/apps/mytardis-hpc-app" \
        + "/resultsready/%s/" % group_id
    values = {'group_id': group_id,
              'experiment_id': experiment_id,
              'files': json.dumps(paths)}
    data = urllib.urlencode(values)
    req = urllib2.Request(destination, data,
            {'Content-Type': 'application/json'})
    response = urllib2.urlopen(req)
    the_page = response.read()

    try:
        info = json.loads(the_page)
    except ValueError as e:
        raise e

    logger.debug("info=%s" % info)
    return info
    #for filename, checksum in info.items():
    #    pass



