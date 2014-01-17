
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

from django import forms
from django.forms.formsets import formset_factory


class NewDirectiveForm1(forms.Form):
    name = forms.CharField(max_length=256, help_text="name")
    description = forms.CharField(
        help_text = "Human Readable name for this directive")

class SchemaForm(forms.Form):
    namespace = forms.CharField(
        label="Namespace",
       help_text="A URI that uniquely ids the schema")
    name = forms.SlugField(
        help_text = "A unique identifier for the schema")
    description = forms.CharField(max_length=80,
                                  help_text="The description of this schema")

class ParameterNameForm(forms.Form):
    name = forms.CharField(max_length=50)
    type = forms.IntegerField()
    parent = forms.CharField(widget=forms.HiddenInput(), required=False)


class DirectiveArgForm(forms.Form):
    namespace = forms.CharField(max_length=80,
                                      help_text="The description of this schema")


SchemaFormSet = formset_factory(SchemaForm, can_delete=True)
DirectiveArgFormSet = formset_factory(DirectiveArgForm, can_delete=True)
ParameterNameFormSet = formset_factory(ParameterNameForm, extra=1, can_delete=True)