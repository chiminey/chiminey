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

import logging
from chiminey.smartconnectorscheduler import models
from chiminey.initialisation import CoreInitial
from django.conf import settings as django_settings


logger = logging.getLogger(__name__)


class WordCountInitial(CoreInitial):
    def get_ui_schema_namespace(self):
        schemas = [
                django_settings.INPUT_FIELDS['hadoop'],
                django_settings.INPUT_FIELDS['location'],
                django_settings.INPUT_FIELDS['wordcount'],
                ]
        return schemas


    def get_domain_specific_schemas(self):
        #schema_data = #{
            #u'%s/input/hrmclight' % django_settings.SCHEMA_PREFIX:
        schema_data =  [u'Word Count Smart Connector',
             {
                 u'word_pattern': {'type': models.ParameterName.STRING, 'subtype': 'string',
                            'description': 'Word Pattern', 'ranking': 0,
                            'initial': "'[a-z.]+'", #TODO regular expression validator/subtype?
                            'help_text': 'Regular expession of filtered words surrounded by single quotes,'},
             }
            ]
        #}
        return schema_data