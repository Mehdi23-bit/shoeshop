from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Shoe, Order
import json
import re
from django.views.decorators.csrf import ensure_csrf_cookie

def _category_thumb(qs):
    """Return the first available shoe image in this queryset, or None."""
    for shoe in qs:
        if shoe.image:
            return shoe.image.url
    return None


@ensure_csrf_cookie
def home(request):
    shoes = Shoe.objects.all().order_by('-created_at')

    men_qs = Shoe.objects.filter(gender='M', is_active=True)
    women_qs = Shoe.objects.filter(gender='W', is_active=True)
    featured_qs = Shoe.objects.filter(is_featured=True, is_active=True)

    categories_preview = [
        {'title': "Men's Collection", 'count': men_qs.count(), 'image': _category_thumb(men_qs)},
        {'title': "Women's Collection", 'count': women_qs.count(), 'image': _category_thumb(women_qs)},
        {'title': 'Limited Edition', 'count': featured_qs.count(), 'image': _category_thumb(featured_qs)},
    ]

    return render(request, 'shoesshop/home.html', {
        'shoes': shoes,
        'categories_preview': categories_preview,
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
    return render(request, 'cart.html', {
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
    return render(request, 'order_confirmation.html', {'order': order})





































































































































































