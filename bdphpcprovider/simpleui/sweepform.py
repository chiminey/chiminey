from django.utils.translation import gettext_lazy as _
from django import forms
from bdphpcprovider.simpleui import validators

class SweepSubmitForm(forms.Form):

    number_vm_instances = forms.IntegerField(
        help_text="Ensure tenancy has sufficient resources")
    minimum_number_vm_instances = forms.IntegerField(
        help_text="Ensure tenancy has sufficient resources", label=("Minimum No. VMs"))
    computation_platform = forms.IntegerField(
        help_text="Ensure tenancy has sufficient resources", label=("Minimum No. VMs"))
    maximum_retry = forms.IntegerField(min_value=0,
        label=_("No. maximum retry after failure"))
    reschedule_failed_processes = forms.BooleanField(initial=True, required=False)

    input_location = forms.CharField(label=_("Input Location"),
        max_length=255,
        help_text="A BDPUrl Directory",
        widget=forms.TextInput
        #widget=forms.Textarea(attrs={'cols': 80, 'rows': 1})
        )
    output_location = forms.CharField(label=_("Output Location"),
        max_length=255,
        help_text="A BDPUrl Directory. Note: The results will also go to MyTardis",
        widget=forms.TextInput
        #widget=forms.Textarea(attrs={'cols': 80, 'rows': 1})
        )

    number_dimensions = forms.IntegerField(min_value=0,
        label=_("No. varying parameters"), help_text="Number of parameters to vary, e.g. 1 = iseed only, 2 = iseed and temp")
    max_iteration = forms.IntegerField(label=("Maximum no. iterations"),min_value=1, help_text="Computation ends when either convergence or maximum iteration reached")
    threshold = forms.CharField(label=_("No. results kept per iteration"),
            max_length=255,
            help_text="Number of outputs to keep between iterations. eg. 2 would keep the top 2 results."
        )
    fanout_per_kept_result = forms.IntegerField(min_value=1,
        label=_("No. fan out per kept result"))
    iseed = forms.IntegerField(min_value=0, help_text="Initial seed for random numbers")
    error_threshold = forms.DecimalField(help_text="Delta for iteration convergence")


    pottype = forms.IntegerField(min_value=0)
    #experiment_id = forms.IntegerField(required=False, help_text="MyTardis experiment number.  Zero for new experiment")
    sweep_map = forms.CharField(label="Values to sweep over", help_text="Dictionary of values to sweep over. e.g {'var1': [3, 7], 'var2': [1, 2]} would result in 4 HRMC Jobs: [3,1] [3,2] [7,1] [7,2] ",
        widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}
        ))

    def __init__(self, *args, **kwargs):
        super(SweepSubmitForm, self).__init__(*args, **kwargs)
        self.fields["sweep_map"].validators.append(validators.validate_sweep_map)
        #self.fields["run_map"].validators.append(validators.validate_run_map)
        self.fields["number_vm_instances"].validators.append(validators.validate_number_vm_instances)
        self.fields["minimum_number_vm_instances"].validators.append(validators.validate_minimum_number_vm_instances)
        self.fields["number_dimensions"].validators.append(validators.validate_number_dimensions)
        self.fields["threshold"].validators.append(validators.validate_threshold)
        self.fields["iseed"].validators.append(validators.validate_iseed)
        self.fields["pottype"].validators.append(validators.validate_pottype)
        self.fields["max_iteration"].validators.append(validators.validate_max_iteration)
        self.fields["error_threshold"].validators.append(validators.validate_error_threshold)
        self.fields["fanout_per_kept_result"].validators.append(validators.validate_fanout_per_kept_result)
        #self.fields["experiment_id"].validators.append(validators.validate_experiment_id)
