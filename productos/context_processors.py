from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.utils.functional import SimpleLazyObject

from .models import Carrito


def _obtener_carrito(request):
    """Busca el carrito y su cantidad total en una sola consulta."""
    if request.user.is_authenticated:
        filtro = {'usuario': request.user}
    else:
        session_key = request.session.session_key
        if not session_key:
            return None
        filtro = {'session_key': session_key}

    return (
        Carrito.objects.filter(**filtro)
        .annotate(cantidad_total=Coalesce(Sum('items__cantidad'), Value(0)))
        .first()
    )


def cart_processor(request):
    """Carrito disponible en los templates, sin consultar si no se usa.

    El panel no muestra el contador del carrito, así que en esas páginas no
    se ejecuta ninguna consulta extra.
    """
    carrito = SimpleLazyObject(lambda: _obtener_carrito(request))

    def cantidad_total():
        return getattr(carrito, 'cantidad_total', 0) or 0

    return {
        'carrito': carrito,
        'carrito_cantidad': SimpleLazyObject(cantidad_total),
    }
