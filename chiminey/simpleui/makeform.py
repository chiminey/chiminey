from django.utils.translation import gettext_lazy as _
import json
from django import forms
from django.core.validators import ValidationError
from chiminey.simpleui import validators

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

    experiment_id = forms.IntegerField(required=False, help_text="MyTardis experiment number.  0 for new experiment")

    sweep_map = forms.CharField(label="Sweep Map JSON",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}
        ))

    def __init__(self, *args, **kwargs):
        super(MakeSubmitForm, self).__init__(*args, **kwargs)
        self.fields["sweep_map"].validators.append(validators.validate_sweep_map)
        self.fields["experiment_id"].validators.append(validators.validate_experiment_id)

