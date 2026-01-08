from django.db import models

class Owner(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)

    razorpay_key_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_key_secret = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name

    
class Building(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    cost = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.owner}"
    

class BuildingImage(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='building_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.building.name}"



class Flat(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='flats')
    flat_number = models.CharField(max_length=20)  
    flat_type = models.CharField(max_length=50)    

    def __str__(self):
        return f"{self.flat_number} ({self.flat_type}) - {self.building.name}"
    

class FlatImage(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='flat_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Flat {self.flat.flat_number}"

