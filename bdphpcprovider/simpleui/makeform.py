from django.utils.translation import gettext_lazy as _
import json
from django import forms
from django.core.validators import ValidationError
from bdphpcprovider.simpleui import validators

class MakeSubmitForm(forms.Form):


    input_location = forms.CharField(label=_("Input Location"),
        max_length=255,
        help_text="A BDPUrl Directory",
        widget=forms.TextInput
        #widget=forms.Textarea(attrs={'cols': 80, 'rows': 1})
        )
    output_location = forms.CharField(label=_("Output Location"),
        max_length=255,
        help_text="A BDPUrl Directory",
        widget=forms.TextInput
        #widget=forms.Textarea(attrs={'cols': 80, 'rows': 1})
        )


    def __init__(self, *args, **kwargs):
        super(MakeSubmitForm, self).__init__(*args, **kwargs)