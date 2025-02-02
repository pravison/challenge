from django import forms 
from .models import  Inquiries
class InquiriesForm(forms.ModelForm):
    class Meta:
        model = Inquiries
        fields = ('website_url', 'name',  'email', 'phone_number')
        widgets = {
            'website_url' : forms.URLInput(attrs={'class': "form-control",  'id': 'website_url', 'placeholder':"Your Website Url"}),
            'name' : forms.TextInput(attrs={'class': "form-control",  'id': 'name', 'placeholder':"Your Full names"}),
            'phone_number' : forms.NumberInput(attrs={'class': "form-control",  'id': 'phone_number', 'placeholder':"use international format ex. 254740562740"}),
            'email' : forms.EmailInput(attrs={'class': "form-control",  'id': 'email', 'placeholder':"(optional) cutomer email"})
			}