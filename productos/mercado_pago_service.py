import mercadopago
from django.conf import settings

class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    def crear_preferencia(self, carrito, items, success_url, failure_url, pending_url, base_url=None):
        """
        Crea una preferencia de pago en Mercado Pago basada en el carrito.
        """
        items_data = []
        for item in items:
            img_url = None
            if item.producto.imagen and base_url:
                img_url = f"{base_url.rstrip('/')}{item.producto.imagen.url}"
            elif item.producto.imagen:
                img_url = item.producto.imagen.url

            items_data.append({
                "id": str(item.producto.id),
                "title": f"{item.producto.nombre} ({item.color.nombre}, {item.talle.abbreviation})",
                "quantity": item.cantidad,
                "unit_price": round(float(item.producto.precio), 2),
                "currency_id": "ARS",
                "picture_url": img_url,
            })

        preference_data = {
            "items": items_data,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            "external_reference": str(carrito.id),
            "statement_descriptor": "CARLOMAGNO",
        }

        # Opcional: Agregar información del cliente si está autenticado
        if carrito.usuario:
            preference_data["payer"] = {
                "name": carrito.usuario.first_name,
                "surname": carrito.usuario.last_name,
                "email": carrito.usuario.email,
            }

        preference_response = self.sdk.preference().create(preference_data)
        
        if preference_response["status"] >= 400:
            raise Exception(f"Error de Mercado Pago: {preference_response['response'].get('message', 'Error desconocido')}")
            
        return preference_response["response"]

    def procesar_pago_tarjeta(self, payment_data):
        """
        Procesa un pago con tarjeta usando los datos enviados por el Card Brick.
        """
        payment_response = self.sdk.payment().create(payment_data)
        
        if payment_response["status"] >= 400:
            error_detail = payment_response['response'].get('message', 'Error desconocido')
            # Intentar obtener más detalles del error si existen
            if 'cause' in payment_response['response']:
                causes = payment_response['response']['cause']
                if isinstance(causes, list) and len(causes) > 0:
                    error_detail = causes[0].get('description', error_detail)
            
            raise Exception(f"Error de pago: {error_detail}")
            
        return payment_response["response"]
