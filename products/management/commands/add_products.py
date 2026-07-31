"""
Replaces the placeholder checkout() from before. Uses your actual Order
model -- generate_order_number() and calculate_totals() already exist there,
they just were never being called.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from decimal import Decimal
from .models import Shoe, Order
from django.http import JsonResponse
from .models import Shoe


@ensure_csrf_cookie
def home(request):
    shoes = Shoe.objects.filter(is_active=True)
    return render(request, 'home.html', {'shoes': shoes})


@ensure_csrf_cookie
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, "Your bag is empty.")
        return redirect('home')

    if request.method == 'POST':
        # Build the `items` JSONField payload your Order model expects
        items_payload = {}
        for shoe_id, data in cart.items():
            quantity = data.get('quantity', 1)
            try:
                shoe = Shoe.objects.get(id=shoe_id)
            except Shoe.DoesNotExist:
                continue
            if shoe.stock < quantity:
                messages.error(request, f"Not enough stock for {shoe.name}.")
                return redirect('cart')
            items_payload[shoe_id] = {
                'price': data.get('price', float(shoe.final_price)),
                'quantity': quantity,
                'size': data.get('size', ''),
            }

        order = Order(
            customer_name=request.POST.get('name'),
            customer_email=request.POST.get('email'),
            customer_phone=request.POST.get('phone'),
            shipping_address=request.POST.get('address'),
            shipping_city=request.POST.get('city'),
            shipping_method=request.POST.get('shipping_method', 'standard'),
            payment_method=request.POST.get('payment_method', 'cash'),
            items=items_payload,
            ip_address=request.META.get('REMOTE_ADDR'),
            session_id=request.session.session_key or '',
        )
        order.calculate_totals()   # this was defined on your model but never called anywhere
        order.save()               # triggers generate_order_number() via your save() override

        # decrement stock now that the order is placed
        for shoe_id, item in items_payload.items():
            shoe = Shoe.objects.get(id=shoe_id)
            shoe.stock = max(0, shoe.stock - item['quantity'])
            shoe.save()

        request.session['cart'] = {}
        request.session.modified = True

        return redirect('order_confirmation', order_number=order.order_number)

    # GET: show the checkout form with a summary of what's in the bag
    items = []
    subtotal = Decimal('0.00')
    for shoe_id, data in cart.items():
        quantity = data.get('quantity', 1)
        try:
            shoe = Shoe.objects.get(id=shoe_id)
        except Shoe.DoesNotExist:
            continue
        item_subtotal = shoe.final_price * quantity
        subtotal += item_subtotal
        items.append({'shoe': shoe, 'quantity': quantity, 'subtotal': item_subtotal})

    return render(request, 'checkout.html', {'cart_items': items, 'subtotal': subtotal})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'order_confirmation.html', {'order': order})



"""
Corrected to match the cart shape your Order.get_items_list() already assumes:
cart = {"<shoe_id>": {"quantity": int, "price": float, "size": str}}
"""

FREE_SHIPPING_THRESHOLD = 100.00
SHIPPING_FLAT_RATE = 5.00


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def add_to_cart(request, shoe_id):
    shoe = get_object_or_404(Shoe, id=shoe_id)

    if shoe.stock <= 0:
        if _is_ajax(request):
            return JsonResponse({'success': False, 'error': f'{shoe.name} is out of stock.'}, status=400)
        return redirect('home')

    size = request.POST.get('size') or request.GET.get('size') or ''

    cart = request.session.get('cart', {})
    key = str(shoe_id)

    if key in cart and isinstance(cart[key], dict):
        cart[key]['quantity'] += 1
    else:
        cart[key] = {
            'quantity': 1,
            'price': float(shoe.final_price),
            'size': size,
        }

    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, 'added': shoe.name, **_cart_data(request)})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def update_cart(request, shoe_id):
    if request.method != 'POST':
        return redirect('cart')

    cart = request.session.get('cart', {})
    key = str(shoe_id)
    action = request.POST.get('action')

    if key in cart:
        if action == 'increase':
            cart[key]['quantity'] += 1
        elif action == 'decrease':
            cart[key]['quantity'] -= 1
            if cart[key]['quantity'] <= 0:
                del cart[key]

    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, **_cart_data(request)})
    return redirect('cart')


def remove_from_cart(request, shoe_id):
    cart = request.session.get('cart', {})
    cart.pop(str(shoe_id), None)
    request.session['cart'] = cart
    request.session.modified = True

    if _is_ajax(request):
        return JsonResponse({'success': True, **_cart_data(request)})
    return redirect('cart')


def _cart_data(request):
    cart = request.session.get('cart', {})
    items = []
    subtotal = 0.0

    for shoe_id, data in cart.items():
        try:
            shoe = Shoe.objects.get(id=shoe_id)
        except Shoe.DoesNotExist:
            continue

        quantity = data.get('quantity', 1)
        price = data.get('price', float(shoe.final_price))
        item_subtotal = price * quantity
        subtotal += item_subtotal

        items.append({
            'id': shoe.id,
            'name': shoe.name,
            'price': price,
            'quantity': quantity,
            'size': data.get('size', ''),
            'subtotal': item_subtotal,
            'image_url': shoe.image.url if getattr(shoe, 'image', None) else None,
        })

    shipping = 0.0 if (subtotal == 0 or subtotal >= FREE_SHIPPING_THRESHOLD) else SHIPPING_FLAT_RATE
    total = subtotal + shipping
    count = sum(item.get('quantity', 0) for item in cart.values())

    return {'items': items, 'subtotal': subtotal, 'shipping': shipping, 'total': total, 'count': count}


def cart_data(request):
    return JsonResponse(_cart_data(request))


@ensure_csrf_cookie
def cart(request):
    data = _cart_data(request)
    return render(request, 'cart.html', {
        'cart_items': data['items'],
        'subtotal': data['subtotal'],
        'shipping': data['shipping'],
        'total': data['total'],
    })
















































































































































































































































































