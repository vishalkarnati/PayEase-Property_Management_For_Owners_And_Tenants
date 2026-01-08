from django import forms
from .models import Tenant

class loginTenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'phone']