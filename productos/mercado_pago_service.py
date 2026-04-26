import mercadopago
from django.conf import settings

class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    def crear_preferencia(self, carrito, items, success_url, failure_url, pending_url):
        """
        Crea una preferencia de pago en Mercado Pago basada en el carrito.
        """
        items_data = []
        for item in items:
            items_data.append({
                "id": str(item.producto.id),
                "title": f"{item.producto.nombre} ({item.color.nombre}, {item.talle.abbreviation})",
                "quantity": item.cantidad,
                "unit_price": float(item.producto.precio),
                "currency_id": "ARS",  # Ajustar según sea necesario
                "picture_url": item.producto.imagen.url if item.producto.imagen else None,
            })

        preference_data = {
            "items": items_data,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            "auto_return": "approved",
            "external_reference": str(carrito.id),
            "statement_descriptor": "Carlo Magno Store",
        }

        # Opcional: Agregar información del cliente si está autenticado
        if carrito.usuario:
            preference_data["payer"] = {
                "name": carrito.usuario.first_name,
                "surname": carrito.usuario.last_name,
                "email": carrito.usuario.email,
            }

        preference_response = self.sdk.preference().create(preference_data)
        return preference_response["response"]
