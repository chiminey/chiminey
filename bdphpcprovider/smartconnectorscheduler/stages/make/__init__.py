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
    settings['username'] = \
        run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_user']
    settings['password'] = \
        run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_password']
    # settings['private_key'] = \
    #         run_settings[
    #             models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key']
    settings['payload_destination'] = \
        run_settings[
        'http://rmit.edu.au/schemas/remotemake/config'][
        'payload_destination']
    settings['input_location'] = run_settings[
        'http://rmit.edu.au/schemas/remotemake']['input_location']
    for key in ['nci_user', 'nci_password']:
        settings[key] = \
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS][key]
    settings['ip'] = run_settings[
        models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    settings['nci_host'] = \
            run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_host']
    settings['output_location'] = \
            run_settings[
                'http://rmit.edu.au/schemas/system/misc'][
                'output_location']

    key_file = ""
    if 'nci_private' in run_settings[models.UserProfile.PROFILE_SCHEMA_NS]:
        if run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key']:
            key_file = hrmcstages.retrieve_private_key(settings,
                run_settings[models.UserProfile.PROFILE_SCHEMA_NS]['nci_private_key'])
    settings['private_key'] = key_file
    settings['nci_private_key'] = key_file
    settings['contextid'] = run_settings[
        'http://rmit.edu.au/schemas/system']['contextid']

    return settings
