from django import forms
from bdphpcprovider.simpleui import validators


class NCIComputationPlatformForm(forms.Form):
    name = forms.CharField(label='Platform Name', required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    ip_address = forms.CharField(label='IP address or Hostname', required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    username = forms.CharField(initial="", required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'required': 'true'}))
    root_path = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    home_path = forms.CharField(required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    private_key_path = forms.CharField(initial='/to/be/generated.pem', widget=forms.HiddenInput(attrs={'class': 'required'}))
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'class': 'required'}))
    filters = forms.CharField(initial='{}', widget=forms.HiddenInput(attrs={'class': 'required'}))