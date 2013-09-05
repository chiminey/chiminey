from django.utils.translation import gettext_lazy as _
import json
from django import forms
from django.core.validators import ValidationError
from bdphpcprovider.simpleui import validators

class SweepSubmitForm(forms.Form):

    number_vm_instances = forms.IntegerField(
        help_text="Ensure tenancy has sufficient resources")
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
    number_dimensions = forms.IntegerField(min_value=0,
        label=_("Degrees of Variation"), help_text="1 = iseed variation, 2 = iseed/temp variation")
    threshold = forms.CharField(label=_("Threshold"),
            max_length=255,
            help_text="Number of outputs to keep between iterations"
        )
    iseed = forms.IntegerField(min_value=0, help_text="Initial seed for random numbers")
    error_threshold = forms.DecimalField(help_text="Delta for interation convergence")

    max_iteration = forms.IntegerField(min_value=1, help_text="Force convergence")
    pottype = forms.IntegerField(min_value=0)
    #experiment_id = forms.IntegerField(required=False, help_text="MyTardis experiment number.  Zero for new experiment")
    sweep_map = forms.CharField(label="Sweep Map JSON", help_text="Dictionary of values to sweep over",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}
        ))
    #run_map = forms.CharField(label="Run Map JSON",
    #    widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}
    #    ))


    def __init__(self, *args, **kwargs):
        super(SweepSubmitForm, self).__init__(*args, **kwargs)
        self.fields["sweep_map"].validators.append(validators.validate_sweep_map)
        #self.fields["run_map"].validators.append(validators.validate_run_map)
        self.fields["number_vm_instances"].validators.append(validators.validate_number_vm_instances)
        self.fields["number_dimensions"].validators.append(validators.validate_number_dimensions)
        self.fields["threshold"].validators.append(validators.validate_threshold)
        self.fields["iseed"].validators.append(validators.validate_iseed)
        self.fields["pottype"].validators.append(validators.validate_pottype)
        self.fields["max_iteration"].validators.append(validators.validate_max_iteration)
        self.fields["error_threshold"].validators.append(validators.validate_error_threshold)
        #self.fields["experiment_id"].validators.append(validators.validate_experiment_id)
