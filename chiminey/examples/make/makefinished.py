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
import json
import logging
import ast

from paramiko.ssh_exception import SSHException
from chiminey.corestages import stage

from chiminey.corestages.stage import Stage

from chiminey import messages
from chiminey.platform import manage
from chiminey import mytardis
from chiminey import storage
from chiminey import compute

from . import setup_settings
from chiminey.sshconnection import open_connection
from chiminey.runsettings import getval, setvals, update, SettingNotFoundException


logger = logging.getLogger(__name__)
RMIT_SCHEMA = "http://rmit.edu.au/schemas"


class MakeFinishedStage(Stage):
    """
    Execute a program using arguments which are local
    """
    def __init__(self, user_settings=None):
        self.user_settings = user_settings.copy()
        pass

    def input_valid(self, settings_to_test):
            return (True, "ok")

    def is_triggered(self, run_settings):

        # if we have no runs_left then we must have finished all the runs
        try:
            runs_left = ast.literal_eval(getval(run_settings, '%s/stages/make/runs_left' % RMIT_SCHEMA))
        except ValueError:
            pass
        except SettingNotFoundException:
            pass
        else:
            # TODO: should check program_success?
            if runs_left:
                try:
                    running = getval(run_settings, '%s/stages/make/running' % RMIT_SCHEMA)
                except SettingNotFoundException:
                    return False
                return running

        return False

        # if self._exists(
        #         run_settings,
        #         'http://rmit.edu.au/schemas/stages/make',
        #         u'runs_left'):
        #     if ast.literal_eval(run_settings[
        #         'http://rmit.edu.au/schemas/stages/make'][
        #         u'runs_left']):
        #         if self._exists(
        #                 run_settings,
        #                 'http://rmit.edu.au/schemas/stages/make',
        #                 u'running'):
        #             return run_settings['http://rmit.edu.au/schemas/stages/make'][
        #                 u'running']

        # return False

    def _job_finished(self, settings, remote_path):

        encoded_d_url = storage.get_url_with_credentials(
            settings=settings,
            url_or_relative_path=remote_path,
            is_relative_path=True,
            ip_address=settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            storage.parse_bdpurl(encoded_d_url)
        stdout = ''
        stderr = ''

        try:
            ssh = open_connection(ip_address=host,
                                                settings=settings)
            (stdout, stderr) = compute.run_make(ssh, (os.path.join(
                query_settings['root_path'], mypath)),
                'running')
        except Exception, e:
            logger.error(e)
            raise
        finally:
            if ssh:
                ssh.close()
        self.program_success = int(not stderr)
        logger.debug("program_success =%s" % self.program_success)
        if not self.program_success:
            logger.debug("command failed, so assuming job still running")
            return False
        self.still_running = 0
        if stdout:
            logger.debug("stdout = %s" % stdout)
            for line in stdout:
                if 'stillrunning' in line:
                    return False
        return True

    def process(self, run_settings):
        self.experiment_id = 0
        local_settings = setup_settings(run_settings)
        self.experiment_id = local_settings['experiment_id']
        messages.info(run_settings, "1: waiting for completion")
        logger.debug("settings=%s" % local_settings)

        try:
            self.runs_left = ast.literal_eval(getval(run_settings, '%s/stages/make/runs_left' % RMIT_SCHEMA))
        except (ValueError, SettingNotFoundException):
            self.runs_left = []

        # if self._exists(run_settings,
        #     'http://rmit.edu.au/schemas/stages/make',
        #     u'runs_left'):
        #     self.runs_left = ast.literal_eval(
        #         run_settings['http://rmit.edu.au/schemas/stages/make'][u'runs_left'])
        # else:
        #     self.runs_left = []

        def _get_dest_bdp_url(local_settings):
            return "%s@%s" % (
                    "nci",
                    os.path.join(local_settings['payload_destination'],
                                 str(local_settings['contextid'])))

        dest_url = _get_dest_bdp_url(local_settings)
        computation_platform_url = local_settings['comp_platform_url']
        bdp_username = local_settings['bdp_username']
        comp_pltf_settings = manage.get_platform_settings(
            computation_platform_url,
            bdp_username)
        local_settings.update(comp_pltf_settings)

        encoded_d_url = storage.get_url_with_credentials(
            local_settings,
            dest_url,
            is_relative_path=True,
            ip_address=local_settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            storage.parse_bdpurl(encoded_d_url)

        if self.runs_left:
            job_finished = self._job_finished(
                settings=local_settings,
                remote_path=dest_url)

            if not job_finished:
                return

            self._get_output(local_settings, dest_url)
            self.runs_left -= 1

        if self.runs_left <= 0:
            messages.success(run_settings, "%s: finished" % (1))

        logger.debug("processing finished")

    def _get_output(self, local_settings, source_url):
        """
            Retrieve the output from the task on the node
        """
        logger.debug("get_output from %s" % source_url)

        computation_platform_url = local_settings['comp_platform_url']
        bdp_username = local_settings['bdp_username']
        comp_pltf_settings = manage.get_platform_settings(
            computation_platform_url,
            bdp_username)
        local_settings.update(comp_pltf_settings)

        encoded_s_url = storage.get_url_with_credentials(
            local_settings,
            source_url,
            is_relative_path=True,
            ip_address=local_settings['host'])

        (scheme, host, mypath, location, query_settings) = \
            storage.parse_bdpurl(encoded_s_url)
        make_path = os.path.join(query_settings['root_path'], mypath)
        logger.debug("make_path=%s" % make_path)

        output_storage_url = local_settings['storeout_platform_url']
        logger.debug("output_storage_url=%s" % output_storage_url)
        output_storage_settings = manage.get_platform_settings(output_storage_url, bdp_username)
        local_settings.update(output_storage_settings)
        logger.debug("output_storage_settings=%s" % output_storage_settings)

        dest_url = '%s://%s@%s/%s/make%s' % (output_storage_settings['scheme'],
                output_storage_settings['type'],
                output_storage_settings['host'],
                    local_settings['storeout_platform_offset'], str(local_settings['contextid']))

        logger.debug("Transferring output from %s to %s" % (source_url,
            dest_url))
        local_settings.update(output_storage_settings)
        encoded_d_url = storage.get_url_with_credentials(local_settings, dest_url)
        logger.debug("encoded_d_url=%s" % encoded_d_url)
        # FIXME: might want to turn on paramiko compress function
        #storage_files(encoded_d_url, exceptions=[])
        # to speed up this transfer
        try:
            storage.copy_directories(encoded_s_url, encoded_d_url)
        except SSHException, e:
            logger.error(e)
            # FIXME: Could just exit, but need to flag that this data has not
            # been transferred.
            raise
        directive = local_settings['directive']

        def _get_mytardis_settings(local_settings, bdp_username):
            mytardis_url = local_settings['mytardis_platform']
            return manage.get_platform_settings(mytardis_url, bdp_username)

        mytardis_settings = _get_mytardis_settings(local_settings, bdp_username)
        logger.debug(mytardis_settings)

        if local_settings['curate_data']:
            if mytardis_settings['mytardis_host']:

                if directive == "vasp":

                 # TODO: this is very domain specific

                    OUTCAR_FILE = "OUTCAR"
                    VALUES_FILE = "values"

                    outcar_url = storage.get_url_with_credentials(local_settings,
                        os.path.join(dest_url, OUTCAR_FILE), is_relative_path=False)
                    logger.debug("outcar_url=%s" % outcar_url)

                    try:
                        outcar_content = storage.get_file(outcar_url)
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

                    values_url = storage.get_url_with_credentials(local_settings,
                        os.path.join(dest_url, VALUES_FILE), is_relative_path=False)
                    logger.debug("values_url=%s" % values_url)
                    try:
                        values_content = storage.get_file(values_url)
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

                    def _get_exp_name_for_vasp(settings, url, path):
                        """
                        Break path based on EXP_DATASET_NAME_SPLIT
                        """
                        return str(os.sep.join(path.split(os.sep)[-2:-1]))

                    def _get_dataset_name_for_vasp(settings, url, path):
                        """
                        Break path based on EXP_DATASET_NAME_SPLIT
                        """
                        encut = settings['ENCUT']
                        numkp = settings['NUMKP']
                        runcounter = settings['RUNCOUNTER']
                        return "%s:encut=%s,num_kp=%s" % (runcounter, encut, numkp)
                        #return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

                    mytardis_settings['ENCUT'] = encut
                    mytardis_settings['NUMKP'] = num_kp
                    mytardis_settings['RUNCOUNTER'] = local_settings['contextid']

                    self.experiment_id = mytardis.create_dataset(
                        settings=mytardis_settings,
                        source_url=encoded_d_url,
                        exp_id=self.experiment_id,
                        exp_name=_get_exp_name_for_vasp,
                        dataset_name=_get_dataset_name_for_vasp,
                        experiment_paramset=[],
                        dataset_paramset=[
                            mytardis.create_paramset("remotemake/output", []),
                            mytardis.create_graph_paramset("dsetgraph",
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
                elif directive == "remotemake":

                    def _get_exp_name_for_make(settings, url, path):
                        return str(os.sep.join(path.split(os.sep)[-2:-1]))

                    def _get_dataset_name_for_make(settings, url, path):
                        return str(os.sep.join(path.split(os.sep)[-1:]))

                    self.experiment_id = mytardis.create_dataset(
                        settings=mytardis_settings,
                        source_url=encoded_d_url,
                        exp_id=self.experiment_id,
                        exp_name=_get_exp_name_for_make,
                        dataset_name=_get_dataset_name_for_make,
                        experiment_paramset=[],
                        dataset_paramset=[
                            mytardis.create_paramset("remotemake/output", [])]
                        )
            else:
                logger.warn("no mytardis host specified")
        else:
            logger.warn('Data curation is off')

    def output(self, run_settings):
        setvals(run_settings, {
                '%s/input/mytardis/experiment_id' % RMIT_SCHEMA: self.experiment_id,
                '%s/stages/make/runs_left' % RMIT_SCHEMA: str(self.runs_left)
        })

        # run_settings['http://rmit.edu.au/schemas/stages/make']['runs_left']  \
        #     = str(self.runs_left)
        # run_settings['http://rmit.edu.au/schemas/input/mytardis']['experiment_id'] \
        #     = self.experiment_id
        # # run_settings['http://rmit.edu.au/schemas/stages/make']['running'] = \
        # #     self.still_running
        return run_settings