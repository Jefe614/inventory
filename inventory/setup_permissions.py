from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from inventory.models import Product, Supplier, PurchaseOrder, SalesOrder

class Command(BaseCommand):
    help = 'Set up groups and permissions for inventory system'

    def handle(self, *args, **kwargs):
        # Create Groups
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        employee_group, _ = Group.objects.get_or_create(name='Employee')

        # Content Types
        product_ct = ContentType.objects.get_for_model(Product)
        supplier_ct = ContentType.objects.get_for_model(Supplier)
        purchase_ct = ContentType.objects.get_for_model(PurchaseOrder)
        sales_ct = ContentType.objects.get_for_model(SalesOrder)

        # Permissions
        permissions = {
            'product': [
                Permission.objects.get_or_create(codename='view_product', name='Can view product', content_type=product_ct)[0],
                Permission.objects.get_or_create(codename='add_product', name='Can add product', content_type=product_ct)[0],
                Permission.objects.get_or_create(codename='change_product', name='Can change product', content_type=product_ct)[0],
                Permission.objects.get_or_create(codename='delete_product', name='Can delete product', content_type=product_ct)[0],
            ],
            'supplier': [
                Permission.objects.get_or_create(codename='view_supplier', name='Can view supplier', content_type=supplier_ct)[0],
                Permission.objects.get_or_create(codename='add_supplier', name='Can add supplier', content_type=supplier_ct)[0],
                Permission.objects.get_or_create(codename='change_supplier', name='Can change supplier', content_type=supplier_ct)[0],
                Permission.objects.get_or_create(codename='delete_supplier', name='Can delete supplier', content_type=supplier_ct)[0],
            ],
            'purchase': [
                Permission.objects.get_or_create(codename='view_purchaseorder', name='Can view purchase order', content_type=purchase_ct)[0],
                Permission.objects.get_or_create(codename='add_purchaseorder', name='Can add purchase order', content_type=purchase_ct)[0],
            ],
            'sales': [
                Permission.objects.get_or_create(codename='view_salesorder', name='Can view sales order', content_type=sales_ct)[0],
                Permission.objects.get_or_create(codename='add_salesorder', name='Can add sales order', content_type=sales_ct)[0],
            ],
        }

        # Assign Permissions
        admin_group.permissions.set(
            permissions['product'] + permissions['supplier'] + permissions['purchase'] + permissions['sales']
        )
        manager_group.permissions.set(
            permissions['product'] + permissions['supplier'] + permissions['purchase'] + permissions['sales']
        )
        employee_group.permissions.set(
            [permissions['product'][0], permissions['purchase'][0], permissions['sales'][0]]  # View only
        )

        self.stdout.write(self.style.SUCCESS('Successfully set up groups and permissions'))