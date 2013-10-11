from django import forms
from bdphpcprovider.simpleui import validators


class NeCTARComputationPlatformForm(forms.Form):
    nectar_username = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    private_key_path = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'required': 'false'}))
