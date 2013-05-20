from django.utils.translation import gettext_lazy as _
from django import forms

class SweepSubmitForm(forms.Form):

    number_vm_instances = forms.IntegerField(min_value=0)
    input_location = forms.CharField(label=_("Input Location"),
        max_length=255,
        widget=forms.TextInput,
    )
    number_of_dimensions = forms.IntegerField(min_value=0, label=_("Degrees of Variation"))
    threshold = forms.CharField(label=_("Threshold"),
            max_length=255,
            widget=forms.TextInput,
        )
    iseed = forms.IntegerField(min_value=0)
    error_threshold = forms.DecimalField()

    max_iteration = forms.IntegerField(min_value=1)
    pottype = forms.IntegerField(min_value=0)


    # ['http://rmit.edu.au/schemas/hrmc',
    #     ('number_vm_instances', 2), (u'iseed', 42),
    #     # TODO: in configure stage could copy this information from somewhere to this required location
    #     ('input_location',  'file://127.0.0.1/hrmcrun/input_0'),
    #     ('number_dimensions', 1),
    #     ('threshold', "[1]"),
    #     ('error_threshold', "0.03"),
    #     ('max_iteration', 20)


