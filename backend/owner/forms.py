from django import forms
from .models import Building, Flat, Owner, BuildingImage
from tenant.models import Tenant

class SignUpOwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['name', 'phone']


class LoginOwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['name', 'phone']


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'address', 'cost']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-2 focus:ring-cyan-700'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-2 focus:ring-cyan-700',
                'rows': 3
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-2 focus:ring-cyan-700'
            }),
        }


class FlatForm(forms.ModelForm):
    class Meta:
        model = Flat
        fields = ['flat_number', 'flat_type']


class addTenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'phone', 'flat_price']