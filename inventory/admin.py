from django.contrib import admin
from .models import Product, Supplier, PurchaseOrder, SalesOrder

admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(PurchaseOrder)
admin.site.register(SalesOrder)