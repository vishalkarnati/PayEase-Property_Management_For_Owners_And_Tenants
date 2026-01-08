from django.db import models
from django.utils import timezone
from owner.models import Flat  

class Tenant(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE, related_name='tenants')
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    flat_price = models.PositiveIntegerField()
    date_added = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)  

    def __str__(self):
        return f"{self.name} in {self.flat.flat_number}"


class RentPayment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="rent_payments")
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE)
    
    amount = models.PositiveIntegerField()
    month = models.CharField(max_length=20)  # Example: "January 2025"
    date_paid = models.DateTimeField(default=timezone.now)

    status = models.CharField(max_length=20, default="PAID")  # PAID / FAILED
    payment_id = models.CharField(max_length=200, blank=True, null=True)  # Razorpay ID

    def __str__(self):
        return f"{self.tenant.name} - {self.month} - {self.amount}"
