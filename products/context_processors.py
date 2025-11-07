# Crear archivo: products/context_processors.py

from .models import Carrito

def cart_processor(request):
    """Context processor para hacer el carrito disponible en todos los templates"""
    carrito = None
    cantidad_total = 0
    
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(usuario=request.user)
            cantidad_total = carrito.get_cantidad_total()
        except Carrito.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                carrito = Carrito.objects.get(session_key=session_key)
                cantidad_total = carrito.get_cantidad_total()
            except Carrito.DoesNotExist:
                pass
    
    return {
        'carrito': carrito,
        'carrito_cantidad': cantidad_total
    }