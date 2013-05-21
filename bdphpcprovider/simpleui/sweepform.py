from django.utils.translation import gettext_lazy as _
import json
from django import forms

class SweepSubmitForm(forms.Form):

    number_vm_instances = forms.IntegerField()
    input_location = forms.CharField(label=_("Input Location"),
        max_length=255,
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 1}))
    number_of_dimensions = forms.IntegerField(min_value=0,
        label=_("Degrees of Variation"), help_text="degrees of freedom")
    threshold = forms.CharField(label=_("Threshold"),
            max_length=255,
            widget=forms.Textarea(attrs={'cols': 10, 'rows': 1}
        ))
    iseed = forms.IntegerField(min_value=0)
    error_threshold = forms.DecimalField()

    max_iteration = forms.IntegerField(min_value=1)
    pottype = forms.IntegerField(min_value=0)
    sweep_map = forms.CharField(label="Sweep Map JSON",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}
        ))
    run_map = forms.CharField(label="Run Map JSON",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}
        ))

    def clean_sweep_map(self):
        sweep_map = self.cleaned_data['sweep_map']
        try:
            map = json.loads(sweep_map)
        except Exception:
            msg = u'JSON is invalid'
            raise forms.ValidationError(msg)
        return sweep_map

    def clean_run_map(self):
        run_map = self.cleaned_data['run_map']
        try:
            map = json.loads(run_map)
        except Exception:
            msg = u'JSON is invalid'
            raise forms.ValidationError(msg)
        return run_map

    def clean_number_vm_instances(self):
        number_vm_instances = self.cleaned_data['number_vm_instances']

        msg = u'number of vm instances should be a positive integer'
        try:
            vms = int(number_vm_instances)
        except ValueError:
            raise forms.ValidationError(msg)

        if vms <= 0:
            raise forms.ValidationError(msg)

        return number_vm_instances

    def clean_number_of_dimensions(self):
        number_of_dimensions = self.cleaned_data['number_of_dimensions']

        msg = u'number of dimensions should be in [1,2]'
        try:
            nd = int(number_of_dimensions)
        except ValueError:
            raise forms.ValidationError(msg)
        if not nd in [1,2]:
            raise forms.ValidationError(msg)
        return number_of_dimensions

    def clean_threshold(self):
        threshold = self.cleaned_data['threshold']

        msg = u'treshold should be "[X]" where X is number of vms to keep'
        try:
            thres = json.loads(threshold)
        except Exception:
            raise forms.ValidationError(msg)
        if len(thres) == 1:
            try:
                th = int(thres[0])
            except IndexError:
                raise forms.ValidationError(msg)
            except ValueError:
                raise forms.ValidationError(msg)
            if th <= 0:
                raise forms.ValidationError(msg)
            return threshold
        raise forms.ValidationError(msg)

    def clean_iseed(self):
        iseed = self.cleaned_data['iseed']

        msg = u'iseed should be a positive integer'
        try:
            vms = int(iseed)
        except ValueError:
            raise forms.ValidationError(msg)

        if vms <= 0:
            raise forms.ValidationError(msg)

        return iseed

    def clean_pottype(self):
        pottype = self.cleaned_data['pottype']

        msg = u'pottype should be a positive integer'
        try:
            vms = int(pottype)
        except ValueError:
            raise forms.ValidationError(msg)
        if vms <= 0:
            raise forms.ValidationError(msg)

        return pottype


    def clean_max_iteration(self):
        max_iteration = self.cleaned_data['max_iteration']

        msg = u'max_iteration should be a positive integer'
        try:
            vms = int(max_iteration)
        except ValueError:
            raise forms.ValidationError(msg)
        if vms <= 0:
            raise forms.ValidationError(msg)

        return max_iteration

    def clean_error_threshold(self):
        error_threshold = self.cleaned_data['error_threshold']

        msg = u'error_threshold should be a positive real'
        try:
            vms = float(error_threshold)
        except ValueError:
            raise forms.ValidationError(msg)
        if vms <= 0:
            raise forms.ValidationError(msg)

        return error_threshold

    # ['http://rmit.edu.au/schemas/hrmc',
    #     ('number_vm_instances', in [0,1],
    #     # TODO: in configure stage could copy this information from somewhere to this required location
    #     ('input_location',  'file://127.0.0.1/hrmcrun/input_0'),
    #     ('number_dimensions', 1),
    #     ('threshold', "[1]"),
    #     ('error_threshold', "0.03"),
    #     ('max_iteration', 20)


