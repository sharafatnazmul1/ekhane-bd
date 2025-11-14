from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, ProductImage
from .forms import ProductForm, CategoryForm, ProductImageForm


@login_required
def product_list(request):
    store = request.user.store

    # Get search and filter parameters
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')

    # Base queryset
    products = Product.objects.filter(store=store).select_related('category')

    # Apply filters
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    elif status == 'featured':
        products = products.filter(is_featured=True)
    elif status == 'low_stock':
        products = [p for p in products if p.is_low_stock]

    # Get categories for filter
    categories = Category.objects.filter(store=store, is_active=True)

    # Statistics
    total_products = Product.objects.filter(store=store).count()
    active_products = Product.objects.filter(store=store, is_active=True).count()
    low_stock_count = len([p for p in Product.objects.filter(store=store, track_inventory=True) if p.is_low_stock])

    context = {
        'store': store,
        'products': products,
        'categories': categories,
        'search': search,
        'selected_category': category_id,
        'selected_status': status,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'dashboard/products/list.html', context)


@login_required
def product_add(request):
    store = request.user.store

    if request.method == 'POST':
        form = ProductForm(request.POST, store=store)

        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()

            messages.success(request, f'Product "{product.name}" has been created successfully!')
            return redirect('product_edit', product_id=product.id)
    else:
        form = ProductForm(store=store)

    context = {
        'store': store,
        'form': form,
        'title': 'Add New Product',
    }
    return render(request, 'dashboard/products/form.html', context)


@login_required
def product_edit(request, product_id):
    store = request.user.store
    product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, store=store)

        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully!')
            return redirect('product_edit', product_id=product.id)
    else:
        form = ProductForm(instance=product, store=store)

    # Get existing images
    images = product.images.all()

    context = {
        'store': store,
        'form': form,
        'product': product,
        'images': images,
        'title': f'Edit: {product.name}',
    }
    return render(request, 'dashboard/products/form.html', context)


@login_required
def product_delete(request, product_id):
    store = request.user.store
    product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully!')
        return redirect('product_list')

    context = {
        'store': store,
        'product': product,
    }
    return render(request, 'dashboard/products/delete.html', context)


@login_required
def product_image_upload(request, product_id):
    store = request.user.store
    product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)

        if form.is_valid():
            image = form.save(commit=False)
            image.product = product
            image.save()

            messages.success(request, 'Image uploaded successfully!')
            return redirect('product_edit', product_id=product.id)

    return redirect('product_edit', product_id=product.id)


@login_required
def product_image_delete(request, image_id):
    store = request.user.store
    image = get_object_or_404(ProductImage, id=image_id, product__store=store)
    product_id = image.product.id

    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully!')

    return redirect('product_edit', product_id=product_id)


@login_required
def category_list(request):
    store = request.user.store
    categories = Category.objects.filter(store=store).select_related('parent')

    context = {
        'store': store,
        'categories': categories,
    }
    return render(request, 'dashboard/categories/list.html', context)


@login_required
def category_add(request):
    store = request.user.store

    if request.method == 'POST':
        form = CategoryForm(request.POST, store=store)

        if form.is_valid():
            category = form.save(commit=False)
            category.store = store
            category.save()

            messages.success(request, f'Category "{category.name}" has been created successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(store=store)

    context = {
        'store': store,
        'form': form,
        'title': 'Add New Category',
    }
    return render(request, 'dashboard/categories/form.html', context)


@login_required
def category_edit(request, category_id):
    store = request.user.store
    category = get_object_or_404(Category, id=category_id, store=store)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, store=store)

        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" has been updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category, store=store)

    context = {
        'store': store,
        'form': form,
        'category': category,
        'title': f'Edit: {category.name}',
    }
    return render(request, 'dashboard/categories/form.html', context)


@login_required
def category_delete(request, category_id):
    store = request.user.store
    category = get_object_or_404(Category, id=category_id, store=store)

    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" has been deleted successfully!')
        return redirect('category_list')

    context = {
        'store': store,
        'category': category,
    }
    return render(request, 'dashboard/categories/delete.html', context)
