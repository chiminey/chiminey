from django import forms
from bdphpcprovider.simpleui import validators


class NCIComputationPlatformForm(forms.Form):
    username = forms.CharField(initial="", required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    private_key_path = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'required': 'false'}))
    filters = forms.CharField(initial='{}', widget=forms.HiddenInput(attrs={'required': 'false'}))