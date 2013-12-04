from django import forms
from bdphpcprovider.simpleui import validators


class MyTardisPlatformForm(forms.Form):
    name = forms.CharField(label='Platform Name', required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    ip_address = forms.CharField(label='IP address or Hostname', required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    username = forms.CharField(initial="", required=True, widget=forms.TextInput(attrs={'required': 'true'}))
    api_key = forms.CharField(label='API Key (recommended)', required=False, widget=forms.TextInput())
    password = forms.CharField(required=False, widget=forms.PasswordInput())
    operation = forms.CharField(initial='update', widget=forms.HiddenInput(attrs={'required': 'true'}))
    filters = forms.CharField(initial='{}', widget=forms.HiddenInput(attrs={'class': 'required'}))
