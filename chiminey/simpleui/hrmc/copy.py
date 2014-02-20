from django.utils.translation import gettext_lazy as _
from django import forms

class CopyForm(forms.Form):

    source_bdp_url = forms.CharField(label=_("Source BDP Url"),
        max_length=255,
        widget=forms.TextInput,
    )

    destination_bdp_url = forms.CharField(label=_("Destination BDP Url"),
        max_length=255,
        widget=forms.TextInput,
    )
