
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

from django import forms
from django.forms.formsets import formset_factory

# FIXME: make API for this info
from bdphpcprovider.smartconnectorscheduler.models import ParameterName, Schema

from bdphpcprovider.simpleui.views import get_subtype_as_choices

RMIT_SCHEMA = "http://rmit.edu.au/schemas"


def unix_find(pathin):
    """Return results similar to the Unix find command run without options
    i.e. traverse a directory tree and return all the file paths
    from http://www.saltycrane.com/blog/2010/04/options-listing-files-directory-python/
    """
    return [os.path.join(path, file)
            for (path, dirs, files) in os.walk(pathin, followlinks=False)
            for file in files]


class NewDirectiveForm1(forms.Form):
    help_text = "Defines schemas"

    name = forms.CharField(max_length=256,
                           widget=forms.TextInput(attrs={'class': 'input-xxlarge', 'size': 80}), help_text="Directive name")
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'input-xxlarge'}),
        required=False,
        help_text="Information about this directive")
    hidden = forms.BooleanField(label="Disabled",
                                required=False,
                                help_text="directive is internal and not visible in UI")


class NewDirectiveForm2(forms.Form):
    help_text = "Defines a directive"

    name = forms.CharField(max_length=256,
                           widget=forms.TextInput(attrs={'class': 'input-xxlarge', 'size': 80}), help_text="Directive name")
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'input-xxlarge'}),
        required=False,
        help_text="Information about this directive")
    hidden = forms.BooleanField(label="Disabled",
                                required=False,
                                help_text="directive is internal and not visible in UI")


class SchemaForm(forms.Form):
    help_text = "Defines a Schema"

    namespace = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'input-xxlarge'}),
        label="Namespace", initial=RMIT_SCHEMA,
       help_text="A URI that uniquely ids the schema")
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input-xxlarge'}),
        help_text="A unique identifier for the schema")
    description = forms.CharField(
        max_length=80, required=False,
        help_text="The description of this schema",
        widget=forms.Textarea(attrs={'class': 'input-xxlarge'}))
    hidden = forms.BooleanField(label="Hidden From UI", required=False,
                                help_text="schema is internal and not visible in UI")


class ParameterNameForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input-xxlarge'}))
    type = forms.ChoiceField(label="Type", choices=ParameterName.TYPES,
                             help_text="The type of the parameter")
    subtype = forms.TypedChoiceField(required=False, label="BDP SubType", choices=get_subtype_as_choices(),
                                help_text="The subtype of the parameter")
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'input-xxlarge'}),
        help_text="Information about this parameter"),
    help_text = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-xxlarge'}),
     help_text="Extra help information for filling out this field")
    parent = forms.CharField(widget=forms.HiddenInput(), required=False)


def get_all_schemas_vars():
    choices = []
    choice = {}
    for param in ParameterName.objects.all():
        sch = param.schema.namespace
        name = param.name
        desc = param.description
        choice.setdefault(sch, []).append((name, desc))

    for sch in sorted(choice.keys()):
        choices.extend(["%s/%s (%s)" % (sch, x[0], x[1]) for x in choice[sch]])

    return [(str(x), str(x)) for x in choices]


class StageParamsForm(forms.Form):
    namespace = forms.ChoiceField(
        label="namespace", choices=get_all_schemas_vars(), required=False,
        help_text="Select variables to set",
        widget=forms.Select(attrs={"class": "input-xxlarge"}))
    value = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'input-xxlarge'}),
                                      help_text="The value of this variable", required=False)


def get_input_schema_choices():
    return [(sch.namespace, "%s (%s)" % (sch.namespace, sch.name)) for sch in Schema.objects.filter(hidden=False).order_by('namespace')]


class InputSchemaForm(forms.Form):
    input_schemas = forms.TypedMultipleChoiceField(choices=get_input_schema_choices(),
        help_text="Choose input schemas",
        widget=forms.SelectMultiple(attrs={'class': 'input-xxlarge'}))


def get_stage_path_choices():
    res = [(x, x) for x in unix_find("/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/stages")]
    return res


class StageSetForm(forms.Form):
    help_text = "Sets the stages"
    legend_text = "Stage Set"
    # stage_set = forms.FilePathField(recursive=True, match='.*\.py$',
    #     path="/opt/cloudenabling/current/bdphpcprovider/smartconnectorscheduler/stages")
    stages_set = forms.TypedMultipleChoiceField(
        choices=get_stage_path_choices(),
        help_text="Select stages to include in this directive",
        widget=forms.SelectMultiple(attrs={'class': 'input-xxlarge'}))
    pass


SchemaFormSet = formset_factory(SchemaForm, can_delete=True)
StageParamsFormSet = formset_factory(StageParamsForm, can_delete=True)
ParameterNameFormSet = formset_factory(ParameterNameForm, extra=1, can_delete=True)


