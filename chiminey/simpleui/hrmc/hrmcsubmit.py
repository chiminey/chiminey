from django.utils.translation import gettext_lazy as _
from django import forms
from chiminey.simpleui import validators


class HRMCSubmitForm(forms.Form):

    number_vm_instances = forms.IntegerField(min_value=0, help_text="Ensure tenancy has sufficient resources")
    minimum_number_vm_instances = forms.IntegerField(
        help_text="Ensure tenancy has sufficient resources", label=("Minimum No. VMs"))
    input_location = forms.CharField(label=_("Input Location"),
        max_length=255,
        widget=forms.TextInput,
        help_text="A BDPUrl Directory"
    )
    output_location = forms.CharField(label=_("Output Location"),
        max_length=255,
        widget=forms.TextInput,
        help_text="A BDPUrl Directory"
#        widget=forms.Textarea(attrs={'cols': 80, 'rows': 1})
        )

    optimisation_scheme = forms.ChoiceField(label=_("Optimisation Scheme"),
        help_text="",
        choices=[("MC","Monte Carlo"), ("MCSA", "Monte Carlo with Simulated Annealing")])
    threshold = forms.CharField(label=_("Threshold"),
            max_length=255,
            widget=forms.TextInput,
            help_text="Number of outputs to keep between iterations"
        )
    iseed = forms.IntegerField(min_value=0,help_text="initial seed for random numbers")
    error_threshold = forms.DecimalField(help_text="delta for interation convergence")

    max_iteration = forms.IntegerField(min_value=1, help_text="Force convergence")
    pottype = forms.IntegerField(min_value=0)
    experiment_id = forms.IntegerField(required=False, help_text="MyTardis experiment number.  Zero for new experiment")

    def __init__(self, *args, **kwargs):
        super(HRMCSubmitForm, self).__init__(*args, **kwargs)
        self.fields["number_vm_instances"].validators.append(validators.validate_number_vm_instances)
        self.fields["minimum_number_vm_instances"].validators.append(validators.validate_minimum_number_vm_instances)
        self.fields["threshold"].validators.append(validators.validate_threshold)
        self.fields["iseed"].validators.append(validators.validate_iseed)
        self.fields["pottype"].validators.append(validators.validate_pottype)
        self.fields["max_iteration"].validators.append(validators.validate_max_iteration)
        self.fields["error_threshold"].validators.append(validators.validate_error_threshold)
        self.fields["experiment_id"].validators.append(validators.validate_experiment_id)




    # ['http://rmit.edu.au/schemas/hrmc',
    #     ('number_vm_instances', 2), (u'iseed', 42),
    #     # TODO: in configure stage could copy this information from somewhere to this required location
    #     ('input_location',  'file://127.0.0.1/hrmcrun/input_0'),
    #     ('optimisation_scheme', 1),
    #     ('threshold', "[1]"),
    #     ('error_threshold', "0.03"),
    #     ('max_iteration', 20)


