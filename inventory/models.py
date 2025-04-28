from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_info = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.IntegerField(default=10)

    def __str__(self):
        return self.name

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date_ordered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase {self.quantity} of {self.product.name}"

class SalesOrder(models.Model):
    STAGE_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date_sold = models.DateTimeField(auto_now_add=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='Pending')

    def __str__(self):
        return f"Sale {self.quantity} of {self.product.name}"

# Signals to update product quantity
@receiver(post_save, sender=PurchaseOrder)
def update_stock_on_purchase(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.quantity += instance.quantity
        product.save()

@receiver(pre_save, sender=SalesOrder)
def update_stock_on_sale(sender, instance, **kwargs):
    if instance.pk:  # Existing order
        old_order = SalesOrder.objects.get(pk=instance.pk)
        if old_order.stage != 'Approved' and instance.stage == 'Approved':
            # Deduct stock when order is approved
            if instance.product.quantity >= instance.quantity:
                instance.product.quantity -= instance.quantity
                instance.product.save()
            else:
                raise ValueError(f"Insufficient stock for {instance.product.name}. Available: {instance.product.quantity}, Requested: {instance.quantity}")
        elif old_order.stage == 'Approved' and instance.stage == 'Rejected':
            # Restore stock if order is rejected
            instance.product.quantity += old_order.quantity
            instance.product.save()
    else:  # New order
        if instance.stage == 'Approved':
            # Deduct stock for new approved orders
            if instance.product.quantity >= instance.quantity:
                instance.product.quantity -= instance.quantity
                instance.product.save()
            else:
                raise ValueError(f"Insufficient stock for {instance.product.name}. Available: {instance.product.quantity}, Requested: {instance.quantity}")