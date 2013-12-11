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


from bdphpcprovider.smartconnectorscheduler import models
from bdphpcprovider.smartconnectorscheduler import hrmcstages


def setup_settings(run_settings):
    settings = {}
    # settings['username'] = \
    #     run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_user']
    # settings['password'] = \
    #     run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_password']


    # settings['private_key'] = \
    #         run_settings[
    #             models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key']
    settings['payload_destination'] = \
        run_settings[
        'http://rmit.edu.au/schemas/remotemake/config'][
        'payload_destination']
    settings['payload_source'] = \
        run_settings[
        'http://rmit.edu.au/schemas/remotemake/config'][
        'payload_source']


    settings['input_location'] = run_settings[
        'http://rmit.edu.au/schemas/input/system']['input_location']
    for key in ['nci_user', 'nci_password']:
        settings[key] = \
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS][key]
    settings['ip'] = run_settings[
        models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    settings['nci_host'] = \
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    settings['output_location'] = \
            run_settings[
                'http://rmit.edu.au/schemas/input/system'][
                'output_location']

    experiment_id = 0
    try:
        experiment_id = int(run_settings['http://rmit.edu.au/schemas/input/mytardis'][u'experiment_id'])
    except ValueError:
        experiment_id = 0
    settings['experiment_id'] = experiment_id

    key_file = ""
    if 'nci_private' in run_settings[models.UserProfile.PROFILE_SCHEMA_NS]:
        if run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key']:
            key_file = hrmcstages.retrieve_private_key(settings,
                run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key'])
    settings['private_key'] = key_file
    settings['nci_private_key'] = key_file
    settings['contextid'] = run_settings[
        'http://rmit.edu.au/schemas/system']['contextid']

    settings['sweep_map'] = run_settings[
            'http://rmit.edu.au/schemas/input/sweep']['sweep_map']

    settings['comp_platform_url'] = run_settings[
            'http://rmit.edu.au/schemas/platform/computation']['platform_url']

    settings['storeout_platform_url'] = run_settings[
            'http://rmit.edu.au/schemas/platform/storage/output']['platform_url']

    settings['storein_platform_offset'] = run_settings[
            'http://rmit.edu.au/schemas/platform/storage/input']['offset']

    settings['storeout_platform_offset'] = run_settings[
            'http://rmit.edu.au/schemas/platform/storage/output']['offset']

    settings['storein_platform_url'] = run_settings[
            'http://rmit.edu.au/schemas/platform/storage/input']['platform_url']

    settings['bdp_username'] = run_settings[
            'http://rmit.edu.au/schemas/bdp_userprofile']['username']


    settings['mytardis_platform'] = run_settings['http://rmit.edu.au/schemas/input/mytardis']['mytardis_platform']

    # settings['mytardis_host'] = \
    #     run_settings[]['mytardis_host']
    # settings['mytardis_user'] = \
    #     run_settings[]['mytardis_user']
    # settings['mytardis_password'] = \
    #     run_settings[]['mytardis_password']

    return settings
