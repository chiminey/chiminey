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


from bdphpcprovider.runsettings import getval, update, SettingNotFoundException


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


def setup_settings(run_settings):
    local_settings = {}

    update(local_settings, run_settings,
           '%s/remotemake/config/payload_destination' % RMIT_SCHEMA,
           '%s/remotemake/config/payload_source' % RMIT_SCHEMA,
           '%s/input/system/input_location' % RMIT_SCHEMA,
           '%s/input/system/output_location' % RMIT_SCHEMA,
           '%s/input/mytardis/mytardis_platform' % RMIT_SCHEMA)

    # settings['payload_destination'] = \
    #     run_settings[
    #     'http://rmit.edu.au/schemas/remotemake/config'][
    #     'payload_destination']
    # settings['payload_source'] = \
    #     run_settings[
    #     'http://rmit.edu.au/schemas/remotemake/config'][
    #     'payload_source']
    # settings['input_location'] = run_settings[
    #     'http://rmit.edu.au/schemas/input/system']['input_location']

    # for key in ['nci_user', 'nci_password']:
    #     settings[key] = \
    #         run_settings[models.UserProfile.PROFILE_SCHEMA_NS][key]

    # settings['ip'] = run_settings[
    #     models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    # settings['nci_host'] = \
    #         run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    # settings['output_location'] = \
    #         run_settings[
    #             'http://rmit.edu.au/schemas/input/system'][
    #             'output_location']

    try:
        experiment_id = int(getval(run_settings, '%s/input/mytardis/experiment_id'))
    except (ValueError, SettingNotFoundException):
        experiment_id = 0
    # experiment_id = 0
    # try:
    #     experiment_id = int(run_settings['http://rmit.edu.au/schemas/input/mytardis'][u'experiment_id'])
    # except ValueError:
    #     experiment_id = 0

    local_settings['experiment_id'] = experiment_id

    # key_file = ""
    # if 'nci_private' in run_settings[models.UserProfile.PROFILE_SCHEMA_NS]:
    #     if run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key']:
    #         key_file = hrmcstages.retrieve_private_key(settings,
    #             run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key'])
    # settings['private_key'] = key_file
    # settings['nci_private_key'] = key_file

    local_settings['contextid'] = getval(run_settings, '%s/system/contextid' % RMIT_SCHEMA)
    local_settings['sweep_map'] = getval(run_settings, '%s/input/sweep/sweep_map' % RMIT_SCHEMA)
    local_settings['comp_platform_url'] = getval(run_settings, '%s/platform/computation/platform_url' % RMIT_SCHEMA)
    local_settings['storeout_platform_url'] = getval(run_settings, '%s/platform/storage/output/platform_url' % RMIT_SCHEMA)
    local_settings['storein_platform_offset'] = getval(run_settings, '%s/platform/storage/input/offset' % RMIT_SCHEMA)
    local_settings['storeout_platform_offset'] = getval(run_settings, '%s/platform/storage/output/offset' % RMIT_SCHEMA)
    local_settings['storein_platform_url'] = getval(run_settings, '%s/platform/storage/input/platform_url' % RMIT_SCHEMA)
    local_settings['bdp_username'] = getval(run_settings, '%s/bdp_userprofile/username' % RMIT_SCHEMA)
    local_settings['directive'] = getval(run_settings, '%s/stages/sweep/directive' % RMIT_SCHEMA)

    # settings['mytardis_platform'] = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']

    return local_settings
