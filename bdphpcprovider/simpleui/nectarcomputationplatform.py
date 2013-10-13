from django import forms
from bdphpcprovider.simpleui import validators


class NeCTARComputationPlatformForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    ec2_secret_key = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    ec2_access_key = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    private_key_path = forms.CharField(initial='/to/be/generated.pem', widget=forms.HiddenInput(attrs={'required': 'false'}))
    private_key = forms.CharField(initial='generated', widget=forms.HiddenInput(attrs={'required': 'false'}))
    vm_image_size = forms.CharField(initial='m1.small', required=False)
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'required': 'false'}))
    filters = forms.CharField(initial='{}', widget=forms.HiddenInput(attrs={'required': 'false'}))