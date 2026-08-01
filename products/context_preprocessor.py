from .views import _normalize_cart


def cart_count(request):
    cart = _normalize_cart(request.session.get('cart', {}))
    return {'cart_count': sum(cart.values())}