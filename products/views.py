from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Shoe, Order
import json
import re
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
from django.utils.text import slugify
def _category_thumb(qs):
    """Return the first available shoe image in this queryset, or None."""
    for shoe in qs:
        if shoe.image:
            return shoe.image.url
    return None


from django.core.paginator import Paginator
from django.db.models import Q

@ensure_csrf_cookie
def home(request):
    shoes_qs = Shoe.objects.filter(is_active=True).order_by('-created_at')

    gender = request.GET.get('gender', '')
    sort = request.GET.get('sort', '')
    search = request.GET.get('q', '').strip()
    stock = request.GET.get('stock', '')

    if gender in ['M', 'W', 'K', 'U']:
        shoes_qs = shoes_qs.filter(gender=gender)

    if search:
        shoes_qs = shoes_qs.filter(Q(name__icontains=search) | Q(brand__icontains=search))

    if stock == 'in':
        shoes_qs = shoes_qs.filter(stock__gt=0)

    if sort == 'price_asc':
        shoes_qs = shoes_qs.order_by('price')
    elif sort == 'price_desc':
        shoes_qs = shoes_qs.order_by('-price')
    elif sort == 'name':
        shoes_qs = shoes_qs.order_by('name')
    else:
        shoes_qs = shoes_qs.order_by('-created_at')

    paginator = Paginator(shoes_qs, 12)  # 12 products per page
    page_obj = paginator.get_page(request.GET.get('page', 1))

    men_qs = Shoe.objects.filter(gender='M', is_active=True)
    women_qs = Shoe.objects.filter(gender='W', is_active=True)
    featured_qs = Shoe.objects.filter(is_featured=True, is_active=True)

    categories_preview = [
        {'title': "Men's Collection", 'count': men_qs.count(), 'image': _category_thumb(men_qs)},
        {'title': "Women's Collection", 'count': women_qs.count(), 'image': _category_thumb(women_qs)},
        {'title': 'Limited Edition', 'count': featured_qs.count(), 'image': _category_thumb(featured_qs)},
    ]

    # Preserve filters across pagination links (page param stripped)
    querydict = request.GET.copy()
    querydict.pop('page', None)
    base_query = querydict.urlencode()

    return render(request, 'shoesshop/home.html', {
        'shoes': page_obj,
        'page_obj': page_obj,
        'categories_preview': categories_preview,
        'current_gender': gender,
        'current_sort': sort,
        'current_search': search,
        'current_stock': stock,
        'base_query': base_query,
    })

def clear_cart(request):
    """Clear entire cart"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.info(request, 'Cart cleared.')
    return redirect('home')

"""
Replaces the previous cart_views.py. Same URLs, same names -- but now
detects whether the request came from fetch() (via the X-Requested-With
header we set in cart.js) and returns JSON in that case instead of
redirecting. Old <form>/<a> based calls still work as a fallback.
"""

SHIPPING_FLAT_RATE = 5.00
FREE_SHIPPING_THRESHOLD = 100.00


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _normalize_cart(cart):
    """
    Older sessions stored each item as a dict like {'quantity': 2, ...}.
    Current code stores a plain int. Coerce anything we find into the
    plain-int format so stale session cookies don't crash the view.
    """
    normalized = {}
    for shoe_id, value in cart.items():
        if isinstance(value, dict):
            qty = value.get('quantity', 0)
        else:
            qty = value
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            qty = 0
        if qty > 0:
            normalized[str(shoe_id)] = qty
    return normalized


def _cart_data(request):
    """Builds the full JSON-serializable cart state -- used by every endpoint below."""
    cart = _normalize_cart(request.session.get('cart', {}))
    request.session['cart'] = cart
    request.session.modified = True

    items = []
    subtotal = 0.0

    for shoe_id, quantity in cart.items():
        try:
            shoe = Shoe.objects.get(id=shoe_id)
        except Shoe.DoesNotExist:
            continue
        item_subtotal = float(shoe.price) * quantity
        subtotal += item_subtotal
        items.append({
            'id': shoe.id,
            'name': shoe.name,
            'price': float(shoe.price),
            'quantity': quantity,
            'subtotal': item_subtotal,
            'image_url': shoe.image.url if shoe.image else None,
        })

    shipping = 0.0 if (subtotal == 0 or subtotal >= FREE_SHIPPING_THRESHOLD) else SHIPPING_FLAT_RATE
    total = subtotal + shipping
    count = sum(cart.values())

    return {
        'items': items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'count': count,
    }


def add_to_cart(request, shoe_id):
    shoe = get_object_or_404(Shoe, id=shoe_id)

    if shoe.stock <= 0:
        if _is_ajax(request):
            return JsonResponse({'success': False, 'error': f'{shoe.name} is out of stock.'}, status=400)
        messages.error(request, f"{shoe.name} is out of stock.")
        return redirect('home')

    cart = _normalize_cart(request.session.get('cart', {}))
    cart[str(shoe_id)] = cart.get(str(shoe_id), 0) + 1
    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, 'added': shoe.name, **_cart_data(request)})

    messages.success(request, f"{shoe.name} added to your bag.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def update_cart(request, shoe_id):
    if request.method != 'POST':
        return redirect('cart')

    cart = _normalize_cart(request.session.get('cart', {}))
    key = str(shoe_id)
    action = request.POST.get('action')

    if key in cart:
        if action == 'increase':
            cart[key] += 1
        elif action == 'decrease':
            cart[key] -= 1
            if cart[key] <= 0:
                del cart[key]

    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, **_cart_data(request)})
    return redirect('cart')


def remove_from_cart(request, shoe_id):
    cart = _normalize_cart(request.session.get('cart', {}))
    cart.pop(str(shoe_id), None)
    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, **_cart_data(request)})
    return redirect('cart')


def cart_data(request):
    """GET endpoint -- used to populate the drawer when it opens, or on page load for the badge."""
    return JsonResponse(_cart_data(request))


def cart(request):
    data = _cart_data(request)
    return render(request, 'shoesshop/cart.html', {
        'cart_items': data['items'],
        'subtotal': data['subtotal'],
        'shipping': data['shipping'],
        'total': data['total'],
    })


def checkout(request):
    data = _cart_data(request)
    return render(request, 'checkout.html', {'cart_items': data['items'], 'subtotal': data['subtotal']})


def get_cart_count(request):
    """AJAX endpoint to get cart count"""
    cart = _normalize_cart(request.session.get('cart', {}))
    count = sum(cart.values())
    return JsonResponse({'count': count})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'shoesshop/order_confirmation.html', {'order': order})


@require_POST
def place_order(request):
    data = _cart_data(request)

    if not data['items']:
        messages.error(request, "Your bag is empty.")
        return redirect('cart')

    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not phone or not address:
        messages.error(request, "Phone number and address are required.")
        return redirect('cart')

    # Build the items JSON the way Order.calculate_totals()/get_items_list() expect
    items_json = {
        str(item['id']): {
            'price': item['price'],
            'quantity': item['quantity'],
        }
        for item in data['items']
    }

    order = Order.objects.create(
        customer_name='Guest',          # no name collected — admin calls to confirm
        customer_email='',              # not collected
        customer_phone=phone,
        shipping_address=address,
        shipping_city='',
        shipping_cost=data['shipping'],
        items=items_json,
        subtotal=data['subtotal'],
        total=data['total'],
        ip_address=request.META.get('REMOTE_ADDR'),
        session_id=request.session.session_key or '',
    )
    order.item_count = sum(v['quantity'] for v in items_json.values())
    order.save()

    # decrement stock
    for shoe_id, item in items_json.items():
        try:
            shoe = Shoe.objects.get(id=int(shoe_id))
            shoe.stock = max(0, shoe.stock - item['quantity'])
            shoe.save()
        except Shoe.DoesNotExist:
            pass

    request.session['cart'] = {}
    request.session.modified = True

    return redirect('order_confirmation', order_number=order.order_number)






def is_staff_user(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_products = Shoe.objects.count()
    out_of_stock = Shoe.objects.filter(stock=0).count()
    low_stock = Shoe.objects.filter(stock__gt=0, stock__lte=5).count()
    recent_orders = Order.objects.all()[:8]
    revenue = Order.objects.filter(payment_status='paid').aggregate(total=Sum('total'))['total'] or 0

    return render(request, 'shoesshop/admin_dashboard.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'revenue': revenue,
    })


@login_required
@user_passes_test(is_staff_user)
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'shoesshop/admin_orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_staff_user)
def admin_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            if new_status == 'delivered' and not order.delivered_at:
                order.delivered_at = timezone.now()
            if new_status == 'cancelled' and not order.cancelled_at:
                order.cancelled_at = timezone.now()
        order.admin_notes = admin_notes
        order.save()
        messages.success(request, f"Order #{order.order_number} updated.")
        return redirect('admin_order_detail', order_number=order.order_number)

    return render(request, 'shoesshop/admin_order_detail.html', {
        'order': order,
        'items': order.get_items_list(),
    })


@login_required
@user_passes_test(is_staff_user)
def admin_products(request):
    products = Shoe.objects.all().order_by('-created_at')
    return render(request, 'shoesshop/admin_products.html', {'products': products})


@login_required
@user_passes_test(is_staff_user)
def admin_product_form(request, shoe_id=None):
    shoe = get_object_or_404(Shoe, id=shoe_id) if shoe_id else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sizes = request.POST.get('sizes', '')
        sizes_list = [s.strip() for s in sizes.split(',') if s.strip()]
        print(sizes_list)
        image = request.FILES.get('image')

        if not shoe:
            shoe = Shoe(slug=slugify(name))

        shoe.name = name
        shoe.brand = request.POST.get('brand', '')
        shoe.price = request.POST.get('price') or 0
        shoe.gender = request.POST.get('gender', 'U')
        shoe.stock = request.POST.get('stock') or 0
        shoe.description = request.POST.get('description', '')
        shoe.sizes = ",".join(sizes_list)
        shoe.is_active = request.POST.get('is_active') == 'on'
        shoe.is_featured = request.POST.get('is_featured') == 'on'
        if image:
            shoe.image = image
        if not shoe.slug:
            shoe.slug = slugify(name)

        shoe.save()
        messages.success(request, f"{shoe.name} saved.")
        return redirect('admin_products')

    return render(request, 'shoesshop/admin_product_form.html', {'shoe': shoe})


@login_required
@user_passes_test(is_staff_user)
@require_POST
def admin_product_delete(request, shoe_id):
    shoe = get_object_or_404(Shoe, id=shoe_id)
    shoe.delete()
    messages.success(request, "Product deleted.")
    return redirect('admin_products')



from django.contrib.auth import authenticate, login, logout


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'admin_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials or you don't have admin access.")

    return render(request, 'shoesshop/admin_login.html', {'next': request.GET.get('next', '')})


def admin_logout(request):
    logout(request)
    messages.success(request, "You've been logged out.")
    return redirect('admin_login')