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


from chiminey.initialisation import CoreInitial

class RandNumCloudInitial(CoreInitial):
    def get_updated_bootstrap_params(self):
        settings = {
                u'http://rmit.edu.au/schemas/stages/setup':
                    {
                        u'payload_source': 'local/payload_randnum',
                        u'payload_destination': 'randnum_dest',
                        u'payload_name': 'process_payload',
                        u'filename_for_PIDs': 'PIDs_collections',
                    },
            }
        return {'settings': settings}

    def get_ui_schema_namespace(self):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schemas = [
                RMIT_SCHEMA + "/input/system/compplatform",
                RMIT_SCHEMA + "/input/system/cloud",
                RMIT_SCHEMA + "/input/location/output",
                ]
        return schemas