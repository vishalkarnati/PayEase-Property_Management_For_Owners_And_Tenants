from django.contrib import admin
from .models import Tenant, RentPayment

admin.site.register(Tenant)

admin.site.register(RentPayment)