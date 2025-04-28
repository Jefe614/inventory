from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import Product, Supplier, PurchaseOrder, SalesOrder
from .forms import ProductForm, SupplierForm, UserRegisterForm, PurchaseOrderForm, SalesOrderForm
from django.db.models import Sum, Count
from django.contrib.auth.decorators import permission_required
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import openpyxl
from django.utils.text import slugify



@login_required
# @permission_required('inventory.view_product', raise_exception=True)
def dashboard(request):
    # Existing data
    products = Product.objects.all()
    low_stock_products = [product for product in products if product.is_low_stock()]
    recent_purchases = PurchaseOrder.objects.order_by('-date_ordered')[:5]
    recent_sales = SalesOrder.objects.order_by('-date_sold')[:5]

    # Total Inventory Value
    total_inventory_value = sum(product.quantity * product.price for product in products)

    # Total Sales and Purchases
    total_sales_quantity = SalesOrder.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_purchases_quantity = PurchaseOrder.objects.aggregate(total=Sum('quantity'))['total'] or 0

    # Top Products
    top_products_by_stock = products.order_by('-quantity')[:5]
    top_products_by_sales = SalesOrder.objects.values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

    # Chart Data (last 7 days)
    today = datetime.now().date()
    last_week = today - timedelta(days=6)
    dates = [(last_week + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    sales_data = []
    purchases_data = []
    for date in dates:
        sales_qty = SalesOrder.objects.filter(date_sold__date=date).aggregate(total=Sum('quantity'))['total'] or 0
        purchases_qty = PurchaseOrder.objects.filter(date_ordered__date=date).aggregate(total=Sum('quantity'))['total'] or 0
        sales_data.append(sales_qty)
        purchases_data.append(purchases_qty)

    context = {
        'products': products,
        'low_stock_products': low_stock_products,
        'recent_purchases': recent_purchases,
        'recent_sales': recent_sales,
        'total_inventory_value': total_inventory_value,
        'total_sales_quantity': total_sales_quantity,
        'total_purchases_quantity': total_purchases_quantity,
        'top_products_by_stock': top_products_by_stock,
        'top_products_by_sales': top_products_by_sales,
        'chart_labels': json.dumps(dates),
        'chart_sales_data': json.dumps(sales_data),
        'chart_purchases_data': json.dumps(purchases_data),
    }
    return render(request, 'dashboard.html', context)

@login_required
# @permission_required('inventory.view_product', raise_exception=True)
def product_list(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

@login_required
# @permission_required('inventory.view_supplier', raise_exception=True)
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'supplier_list.html', {'suppliers': suppliers})

@login_required
# @permission_required('inventory.view_purchaseorder', raise_exception=True)
def purchase_list(request):
    purchases = PurchaseOrder.objects.all()
    return render(request, 'purchase_list.html', {'purchases': purchases})

@login_required
# @permission_required('inventory.view_salesorder', raise_exception=True)
def sales_list(request):
    sales = SalesOrder.objects.all()
    return render(request, 'sales_list.html', {'sales': sales})

# Product CRUD
@login_required
# @permission_required('inventory.add_product', raise_exception=True)
def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
# @permission_required('inventory.change_product', raise_exception=True)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'product_form.html', {'form': form, 'title': 'Edit Product'})

@login_required
# @permission_required('inventory.delete_product', raise_exception=True)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('product_list')

# Supplier CRUD
@login_required
# @permission_required('inventory.add_supplier', raise_exception=True)
def supplier_add(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'supplier_form.html', {'form': form, 'title': 'Add Supplier'})

@login_required
# @permission_required('inventory.change_supplier', raise_exception=True)
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'supplier_form.html', {'form': form, 'title': 'Edit Supplier'})

@login_required
# @permission_required('inventory.delete_supplier', raise_exception=True)
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.delete()
    messages.success(request, 'Supplier deleted successfully.')
    return redirect('supplier_list')

# Purchase Order CRUD
@login_required
# @permission_required('inventory.add_purchaseorder', raise_exception=True)
def purchase_add(request):
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase order added successfully.')
            return redirect('purchase_list')
    else:
        form = PurchaseOrderForm()
    return render(request, 'purchase_form.html', {'form': form, 'title': 'Add Purchase Order'})

# Sales Order CRUD
@login_required
# @permission_required('inventory.add_salesorder', raise_exception=True)
def sales_add(request):
    if request.method == "POST":
        form = SalesOrderForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Sales order added successfully.')
                return redirect('sales_list')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = SalesOrderForm()
    return render(request, 'sales_form.html', {'form': form, 'title': 'Add Sales Order'})

@login_required
# @permission_required('inventory.add_salesorder', raise_exception=True)
def sales_edit(request, pk):
    sale = get_object_or_404(SalesOrder, pk=pk)
    if request.method == "POST":
        form = SalesOrderForm(request.POST, instance=sale)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Sales order updated successfully.')
                return redirect('sales_list')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = SalesOrderForm(instance=sale)
    return render(request, 'sales_form.html', {'form': form, 'title': 'Edit Sales Order'})

@login_required
# @permission_required('inventory.add_salesorder', raise_exception=True)
def sales_delete(request, pk):
    sale = get_object_or_404(SalesOrder, pk=pk)
    if sale.stage == 'Approved':
        sale.product.quantity += sale.quantity  # Restore stock
        sale.product.save()
    sale.delete()
    messages.success(request, 'Sales order deleted successfully.')
    return redirect('sales_list')

@login_required
# @permission_required('inventory.add_salesorder', raise_exception=True)
def sales_update_stage(request, pk):
    sale = get_object_or_404(SalesOrder, pk=pk)
    if request.method == "POST":
        stage = request.POST.get('stage')
        if stage in dict(SalesOrder.STAGE_CHOICES).keys():
            try:
                sale.stage = stage
                sale.save()
                messages.success(request, f'Sales order stage updated to {stage}.')
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Invalid stage selected.')
    return redirect('sales_list')

# Authentication
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            employee_group = Group.objects.get(name='Employee')
            user.groups.add(employee_group)
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            return render(request, 'register.html', {'form': form})
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
# @permission_required('inventory.view_product', raise_exception=True)
def reports(request):
    # Inventory Summary
    products = Product.objects.all()
    total_inventory_value = sum(product.quantity * product.price for product in products)
    total_stock = sum(product.quantity for product in products)
    # Calculate value for each product
    products_with_value = [
        {
            'name': product.name,
            'quantity': product.quantity,
            'price': product.price,
            'value': product.quantity * product.price
        } for product in products
    ]

    # Low-Stock Products
    low_stock_products = [product for product in products if product.is_low_stock()]

    # Fast-Moving Products (top 10 by sales in last 30 days)
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    fast_moving_products = SalesOrder.objects.exclude(stage='Rejected')\
        .filter(date_sold__date__gte=thirty_days_ago)\
        .values('product__name')\
        .annotate(total_sold=Sum('quantity'))\
        .order_by('-total_sold')[:10]

    # Sales Report (last 30 days, grouped by stage)
    sales_summary = SalesOrder.objects.filter(date_sold__date__gte=thirty_days_ago)\
        .values('stage')\
        .annotate(total_quantity=Sum('quantity'), total_orders=Count('id'))\
        .order_by('stage')

    # Purchase Report (last 30 days)
    purchase_summary = PurchaseOrder.objects.filter(date_ordered__date__gte=thirty_days_ago)\
        .values('product__name')\
        .annotate(total_quantity=Sum('quantity'), total_orders=Count('id'))\
        .order_by('-total_quantity')

    context = {
        'total_inventory_value': total_inventory_value,
        'total_stock': total_stock,
        'products_with_value': products_with_value,  # Updated key
        'low_stock_products': low_stock_products,
        'fast_moving_products': fast_moving_products,
        'sales_summary': sales_summary,
        'purchase_summary': purchase_summary,
    }
    return render(request, 'reports.html', context)

# Update export_report to use products_with_value for inventory report
@login_required
# @permission_required('inventory.view_product', raise_exception=True)
def export_report(request, report_type, format_type):
    if report_type == 'inventory':
        data = Product.objects.all()
        title = "Inventory Summary Report"
        headers = ['Name', 'Quantity', 'Price', 'Value']
        rows = [[p.name, p.quantity, p.price, p.quantity * p.price] for p in data]
    elif report_type == 'low_stock':
        data = [p for p in Product.objects.all() if p.is_low_stock()]
        title = "Low Stock Report"
        headers = ['Name', 'Quantity', 'Low Stock Threshold']
        rows = [[p.name, p.quantity, p.low_stock_threshold] for p in data]
    elif report_type == 'fast_moving':
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        data = SalesOrder.objects.exclude(stage='Rejected')\
            .filter(date_sold__date__gte=thirty_days_ago)\
            .values('product__name')\
            .annotate(total_sold=Sum('quantity'))\
            .order_by('-total_sold')[:10]
        title = "Fast-Moving Products Report"
        headers = ['Product Name', 'Total Sold (Kg)']
        rows = [[d['product__name'], d['total_sold']] for d in data]
    elif report_type == 'sales':
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        data = SalesOrder.objects.filter(date_sold__date__gte=thirty_days_ago)\
            .values('stage')\
            .annotate(total_quantity=Sum('quantity'), total_orders=Count('id'))\
            .order_by('stage')
        title = "Sales Summary Report"
        headers = ['Stage', 'Total Quantity (Kg)', 'Total Orders']
        rows = [[d['stage'], d['total_quantity'], d['total_orders']] for d in data]
    elif report_type == 'purchases':
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        data = PurchaseOrder.objects.filter(date_ordered__date__gte=thirty_days_ago)\
            .values('product__name')\
            .annotate(total_quantity=Sum('quantity'), total_orders=Count('id'))\
            .order_by('-total_quantity')
        title = "Purchase Summary Report"
        headers = ['Product Name', 'Total Quantity (Kg)', 'Total Orders']
        rows = [[d['product__name'], d['total_quantity'], d['total_orders']] for d in data]
    else:
        return HttpResponse("Invalid report type", status=400)

    if format_type == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, title)
        p.setFont("Helvetica", 12)
        p.drawString(100, 730, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        y = 700
        p.setFont("Helvetica-Bold", 12)
        for i, header in enumerate(headers):
            p.drawString(100 + i * 100, y, header)
        p.setFont("Helvetica", 10)
        y -= 20
        
        for row in rows:
            for i, item in enumerate(row):
                p.drawString(100 + i * 100, y, str(item))
            y -= 20
            if y < 50:
                p.showPage()
                y = 750
        
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{slugify(title)}.pdf"'
        return response

    elif format_type == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title
        ws.append([title])
        ws.append([f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
        ws.append([])
        ws.append(headers)
        for row in rows:
            ws.append(row)
        
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column].width = adjusted_width

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{slugify(title)}.xlsx"'
        return response

    return HttpResponse("Invalid format type", status=400)