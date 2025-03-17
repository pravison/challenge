from django import forms 
from .models import LoyaltyPointsCategory, Staff

class EditLoyaltyPointsCategoryForm(forms.ModelForm):
    class Meta:
        model = LoyaltyPointsCategory
        fields = ('category', 'total_value_for_a_point', 'redemed_at_how_much_per_point')
        widgets = {
            'category': forms.Select(attrs={'class': "form-control",  'id': 'category', 'placeholder':"select category"} ),
            'total_value_for_a_point': forms.NumberInput(attrs={'class': "form-control",  'id': 'total_value_for_a_point', 'placeholder':"Enter the Total Value that equals a point"}  ),  
            'redemed_at_how_much_per_point' : forms.NumberInput(attrs={'class': "form-control",  'id': 'redemed_at_how_much_per_point', 'placeholder':"at how much will you reddem a point"}),
			}