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

import os
import json
import logging
import ast
import logging.config

from bdphpcprovider.smartconnectorscheduler.smartconnector import Stage
from bdphpcprovider.smartconnectorscheduler import sshconnector
from bdphpcprovider.smartconnectorscheduler import smartconnector
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import platform


from bdphpcprovider.smartconnectorscheduler import mytardis
from bdphpcprovider.smartconnectorscheduler.stages.composite import (make_graph_paramset, make_paramset)
from paramiko.ssh_exception import SSHException


from . import setup_settings

logger = logging.getLogger(__name__)


class MakeFinishedStage(Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def input_valid(self, settings_to_test):
            return (True, "ok")

    def triggered(self, run_settings):

        # if we have no runs_left then we must have finished all the runs
        if self._exists(
                run_settings,
                'http://rmit.edu.au/schemas/stages/make',
                u'runs_left'):
            if ast.literal_eval(run_settings[
                'http://rmit.edu.au/schemas/stages/make'][
                u'runs_left']):
                if self._exists(
                        run_settings,
                        'http://rmit.edu.au/schemas/stages/make',
                        u'running'):
                    return run_settings['http://rmit.edu.au/schemas/stages/make'][
                        u'running']

        return False

    def _job_finished(self, settings, remote_path):

        encoded_d_url = smartconnector.get_url_with_pkey(
            settings=settings,
            url_or_relative_path=remote_path,
            is_relative_path=True,
            ip_address=settings['host'])
        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_d_url)
        command = "cd %s; make %s" % (os.path.join(
                query_settings['root_path'], mypath),
            'running')
        command_out = ''
        errs = ''
        logger.debug("starting command %s for %s" % (command, host))
        # TODO: need to try this command a few times if fails.
        ssh = None
        try:
            ssh = sshconnector.open_connection(ip_address=host,
                                                settings=settings)
            command_out, errs = sshconnector.run_command_with_status(ssh, command)
        except Exception, e:
            logger.error(e)
        finally:
            if ssh:
                ssh.close()
        logger.debug("command_out2=(%s, %s)" % (command_out, errs))
        if not errs:
            self.program_success = True
        else:
            self.program_success = False

        logger.debug("program_success =%s" % self.program_success)

        if not self.program_success:
            logger.debug("command failed, so assuming job still running")
            return False

        self.still_running = 0
        if command_out:
            logger.debug("command_out = %s" % command_out)
            for line in command_out:
                if 'stillrunning' in line:
                    return False
        return True

    def process(self, run_settings):
        self.experiment_id = 0
        settings = setup_settings(run_settings)
        self.experiment_id = settings['experiment_id']
        logger.debug("settings=%s" % settings)
        if self._exists(run_settings,
            'http://rmit.edu.au/schemas/stages/make',
            u'runs_left'):
            self.runs_left = ast.literal_eval(
                run_settings['http://rmit.edu.au/schemas/stages/make'][u'runs_left'])
        else:
            self.runs_left = []

        def _get_dest_bdp_url(settings):
            return "%s@%s" % (
                    "nci",
                    os.path.join(settings['payload_destination'],
                                 str(settings['contextid'])))

        dest_url = _get_dest_bdp_url(settings)
        computation_platform_url = settings['comp_platform_url']
        bdp_username = settings['bdp_username']
        comp_pltf_settings = platform.get_platform_settings(
            computation_platform_url,
            bdp_username)
        settings.update(comp_pltf_settings)

        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            dest_url,
            is_relative_path=True,
            ip_address=settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_d_url)

        if self.runs_left:
            job_finished = self._job_finished(
                settings=settings,
                remote_path=dest_url)

            if not job_finished:
                return

            self._get_output(settings, dest_url)
            self.runs_left -= 1

        if self.runs_left <= 0:
            smartconnector.success(run_settings, "%s: finished" % (1))

        logger.debug("processing finished")

    def _get_output(self, settings, source_url):
        """
            Retrieve the output from the task on the node
        """
        logger.debug("get_output from %s" % source_url)

        computation_platform_url = settings['comp_platform_url']
        bdp_username = settings['bdp_username']
        comp_pltf_settings = platform.get_platform_settings(
            computation_platform_url,
            bdp_username)
        settings.update(comp_pltf_settings)

        encoded_s_url = smartconnector.get_url_with_pkey(
            settings,
            source_url,
            is_relative_path=True,
            ip_address=settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            hrmcstages.parse_bdpurl(encoded_s_url)
        make_path = os.path.join(query_settings['root_path'], mypath)
        logger.debug("make_path=%s" % make_path)

        output_storage_url = settings['storeout_platform_url']
        logger.debug("output_storage_url=%s" % output_storage_url)
        output_storage_settings = platform.get_platform_settings(output_storage_url, bdp_username)
        settings.update(output_storage_settings)
        logger.debug("output_storage_settings=%s" % output_storage_settings)

        dest_url = '%s://%s@%s/%s/make%s' % (output_storage_settings['scheme'],
                output_storage_settings['type'],
                output_storage_settings['host'],
                    settings['storeout_platform_offset'], str(settings['contextid']))

        logger.debug("Transferring output from %s to %s" % (source_url,
            dest_url))
        settings.update(output_storage_settings)

        encoded_d_url = smartconnector.get_url_with_pkey(settings, dest_url)

        # encoded_d_url = smartconnector.get_url_with_pkey(
        #     settings,
        #     dest_url, is_relative_path=False, ip_address=settings['host'])
        logger.debug("encoded_d_url=%s" % encoded_d_url)

        #hrmcstages.delete_files(encoded_d_url, exceptions=[])

        # FIXME: might want to turn on paramiko compress function
        # to speed up this transfer
        try:
            hrmcstages.copy_directories(encoded_s_url, encoded_d_url)
        except SSHException, e:
            logger.error(e)
            # FIXME: Could just exit, but need to flag that this data has not
            # been transferred.
            raise

        # TODO: this is very domain specific
        if settings['mytardis_host']:

            OUTCAR_FILE = "OUTCAR"
            VALUES_FILE = "values"

            outcar_url = smartconnector.get_url_with_pkey(settings,
                os.path.join(dest_url, OUTCAR_FILE), is_relative_path=False)
            logger.debug("outcar_url=%s" % outcar_url)

            try:
                outcar_content = hrmcstages.get_file(outcar_url)
            except IOError, e:
                logger.error(e)
                toten = None
            else:
                toten = None
                for line in outcar_content.split('\n'):
                    #logger.debug("line=%s" % line)
                    if 'e  en' in line:
                        logger.debug("found")
                        try:
                            toten = float(line.rsplit(' ', 2)[-2])
                        except ValueError, e:
                            logger.error(e)
                            pass
                        break

            logger.debug("toten=%s" % toten)

            values_url = smartconnector.get_url_with_pkey(settings,
                os.path.join(dest_url, VALUES_FILE), is_relative_path=False)
            logger.debug("values_url=%s" % values_url)
            try:
                values_content = hrmcstages.get_file(values_url)
            except IOError, e:
                logger.error(e)
                values = None
            else:
                values = None
                try:
                    values = dict(json.loads(values_content))
                except Exception, e:
                    logger.error(e)
                    pass

            logger.debug("values=%s" % values)

            # FIXME: all values from map are strings initially, so need to know
            # type to coerce.
            num_kp = None
            if 'num_kp' in values:
                try:
                    num_kp = int(values['num_kp'])
                except IndexError:
                    pass
                except ValueError:
                    pass

            logger.debug("num_kp=%s" % num_kp)

            encut = None
            if 'encut' in values:
                try:
                    encut = int(values['encut'])
                except IndexError:
                    pass
                except ValueError:
                    pass
            logger.debug("encut=%s" % encut)

            EXP_DATASET_NAME_SPLIT = 1

            def _get_exp_name_for_make(settings, url, path):
                """
                Break path based on EXP_DATASET_NAME_SPLIT
                """
                return str(os.sep.join(path.split(os.sep)[-(EXP_DATASET_NAME_SPLIT + 1):]))

            def _get_dataset_name_for_make(settings, url, path):
                """
                Break path based on EXP_DATASET_NAME_SPLIT
                """
                encut = settings['ENCUT']
                numkp = settings['NUMKP']
                runcounter = settings['RUNCOUNTER']
                return "%s:encut=%s,num_kp=%s" % (runcounter, encut, numkp)
                #return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

            settings['ENCUT'] = encut
            settings['NUMKP'] = num_kp
            settings['RUNCOUNTER'] = settings['contextid']
            # TODO: THIS IS
            self.experiment_id = mytardis.post_dataset(
                settings=settings,
                source_url=encoded_d_url,
                exp_id=self.experiment_id,
                exp_name=_get_exp_name_for_make,
                dataset_name=_get_dataset_name_for_make,
                experiment_paramset=[
                    make_paramset("remotemake", []),
                    make_graph_paramset("expgraph",
                        name="makeexp1",
                        graph_info={"axes":["num_kp", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp", "makedset/toten"]]),
                    make_graph_paramset("expgraph",
                        name="makeexp2",
                        graph_info={"axes":["encut", "energy"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/encut", "makedset/toten"]]),
                    make_graph_paramset("expgraph",
                        name="makeexp3",
                        graph_info={"axes":["num_kp", "encut", "TOTEN"], "legends":["TOTEN"]},
                        value_dict={},
                        value_keys=[["makedset/num_kp", "makedset/encut", "makedset/toten"]]),
                ],
                dataset_paramset=[
                    make_paramset("remotemake/output", []),
                    make_graph_paramset("dsetgraph",
                        name="makedset",
                        graph_info={},
                        value_dict={"makedset/num_kp": num_kp, "makedset/encut": encut, "makedset/toten": toten}
                            if (num_kp is not None)
                                and (encut is not None)
                                and (toten is not None) else {},
                        value_keys=[]
                        ),
                    ]
               )

    def output(self, run_settings):
        run_settings['http://rmit.edu.au/schemas/stages/make']['runs_left']  \
            = str(self.runs_left)
        run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] \
            = self.experiment_id
        # run_settings['http://rmit.edu.au/schemas/stages/make']['running'] = \
        #     self.still_running
        return run_settings