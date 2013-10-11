from django import forms
from bdphpcprovider.simpleui import validators


class NCIComputationPlatformForm(forms.Form):
    username = forms.CharField(initial="", required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    private_key_path = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'required': 'false'}))

    def __init__(self, *args, **kwargs):
        super(NCIComputationPlatformForm, self).__init__(*args, **kwargs)
        #self.fields["username"].validators.append(validators.validate_not_null)
        #self.fields["run_map"].validators.append(validators.validate_run_map)
        #self.fields["private_key_path"].validators.append(validators.validate_not_null)


