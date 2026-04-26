from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Carrito, CarritoItem, Producto, Color, Talle, ProductoStock
import json

def get_or_create_cart(request):
    """Obtiene o crea un carrito para el usuario actual"""
    if request.user.is_authenticated:
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        carrito, created = Carrito.objects.get_or_create(session_key=session_key)
    
    return carrito

def get_cart_data(request):
    """Obtiene los datos del carrito en formato JSON para el navbar"""
    carrito = get_or_create_cart(request)
    items = []
    
    for item in carrito.items.select_related('producto', 'color', 'talle'):
        items.append({
            'id': item.id,
            'producto_id': item.producto.id,
            'nombre': item.producto.nombre,
            'imagen': item.producto.imagen.url if item.producto.imagen else None,
            'color': item.color.nombre,
            'color_hex': item.color.hex_code,
            'talle': item.talle.abbreviation,
            'precio': str(item.producto.precio),
            'cantidad': item.cantidad,
            'subtotal': str(item.get_subtotal()),
            'stock_disponible': item.get_stock_disponible()
        })
    
    return JsonResponse({
        'items': items,
        'cantidad_total': carrito.get_cantidad_total(),
        'total': str(carrito.get_total())
    })

@require_POST
def agregar_al_carrito(request):
    """Agrega un producto al carrito"""
    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        color_id = data.get('color_id')
        talle_id = data.get('talle_id')
        cantidad = int(data.get('cantidad', 1))
        
        # Validar datos
        if not all([producto_id, color_id, talle_id]):
            return JsonResponse({
                'success': False,
                'message': 'Faltan datos requeridos'
            }, status=400)
        
        # Obtener objetos
        producto = get_object_or_404(Producto, id=producto_id)
        color = get_object_or_404(Color, id=color_id)
        talle = get_object_or_404(Talle, id=talle_id)
        
        # Verificar stock disponible
        try:
            stock = ProductoStock.objects.get(
                producto=producto,
                color=color,
                talle=talle
            )
        except ProductoStock.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No hay stock disponible para esta combinación'
            }, status=400)
        
        # Obtener o crear carrito
        carrito = get_or_create_cart(request)
        
        # Buscar si ya existe este item en el carrito
        item, created = CarritoItem.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            color=color,
            talle=talle,
            defaults={'cantidad': 0}  # Iniciar en 0 para sumar después
        )
        
        # Calcular nueva cantidad
        nueva_cantidad = item.cantidad + cantidad
        
        # Verificar que no exceda el stock
        if nueva_cantidad > stock.stock:
            stock_disponible = stock.stock - item.cantidad
            if stock_disponible <= 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Ya tienes el máximo disponible ({item.cantidad} unidades) en el carrito'
                }, status=400)
            return JsonResponse({
                'success': False,
                'message': f'Solo puedes agregar {stock_disponible} unidades más. Stock total: {stock.stock}'
            }, status=400)
        
        # Actualizar cantidad
        item.cantidad = nueva_cantidad
        item.save()
        
        mensaje = f'Se {"agregó" if created else "actualizó"} el producto en el carrito'
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'cantidad_item': item.cantidad,
            'cantidad_total': carrito.get_cantidad_total(),
            'total': str(carrito.get_total())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_POST
def actualizar_cantidad(request):
    """Actualiza la cantidad de un item en el carrito"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        cantidad = int(data.get('cantidad', 1))
        
        if cantidad < 1:
            return JsonResponse({
                'success': False,
                'message': 'La cantidad debe ser al menos 1'
            }, status=400)
        
        carrito = get_or_create_cart(request)
        item = get_object_or_404(CarritoItem, id=item_id, carrito=carrito)
        
        # Verificar stock
        stock_disponible = item.get_stock_disponible()
        if cantidad > stock_disponible:
            return JsonResponse({
                'success': False,
                'message': f'Solo hay {stock_disponible} unidades disponibles'
            }, status=400)
        
        item.cantidad = cantidad
        item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cantidad actualizada',
            'subtotal': str(item.get_subtotal()),
            'cantidad_total': carrito.get_cantidad_total(),
            'total': str(carrito.get_total())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_POST
def eliminar_item_del_carrito(request):
    """Elimina un item del carrito"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        carrito = get_or_create_cart(request)
        item = get_object_or_404(CarritoItem, id=item_id, carrito=carrito)
        item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado del carrito',
            'cantidad_total': carrito.get_cantidad_total(),
            'total': str(carrito.get_total())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

def vaciar_carrito(request):
    """Vacía el carrito completamente"""
    carrito = get_or_create_cart(request)
    carrito.items.all().delete()
    return JsonResponse({"success": True, "message": "Carrito vaciado correctamente"})

from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .mercado_pago_service import MercadoPagoService
from .models import Cliente, Direccion
from django.conf import settings

@login_required(login_url='login_cliente')
def checkout_view(request):
    """Muestra la página de checkout con datos de facturación"""
    carrito = get_or_create_cart(request)
    items = carrito.items.all()
    
    if not items:
        messages.warning(request, "Tu carrito está vacío")
        return redirect('productos')
        
    try:
        cliente = Cliente.objects.get(email=request.user.email)
    except Cliente.DoesNotExist:
        cliente = Cliente.objects.create(
            nombre=request.user.first_name,
            apellidos=request.user.last_name,
            email=request.user.email,
            activado=True
        )
        
    direccion = cliente.direcciones.filter(es_predeterminada=True).first()
    if not direccion:
        direccion = cliente.direcciones.first()
            
    return render(request, 'checkout.html', {
        'carrito': carrito,
        'items': items,
        'cliente': cliente,
        'direccion': direccion,
        'total': carrito.get_total(),
        'MERCADO_PAGO_PUBLIC_KEY': settings.MERCADO_PAGO_PUBLIC_KEY
    })

@login_required(login_url='login_cliente')
def iniciar_pago_mercadopago(request):
    """Crea una preferencia de Mercado Pago y redirige al usuario"""
    try:
        carrito = get_or_create_cart(request)
        items = carrito.items.all()
        
        if not items:
            return JsonResponse({"success": False, "message": "El carrito está vacío"}, status=400)
            
        mp_service = MercadoPagoService()
        
        # Construir URLs de retorno
        success_url = request.build_absolute_uri(reverse('pago_exitoso'))
        failure_url = request.build_absolute_uri(reverse('pago_fallido'))
        pending_url = request.build_absolute_uri(reverse('pago_pendiente'))
        
        base_url = request.build_absolute_uri('/')
        preference = mp_service.crear_preferencia(
            carrito, 
            items, 
            success_url, 
            failure_url, 
            pending_url,
            base_url=base_url
        )
        
        return JsonResponse({
            "success": True,
            "preference_id": preference.get("id"),
            "init_point": preference.get("init_point")
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@require_POST
@login_required(login_url='login_cliente')
def procesar_pago_tarjeta(request):
    """Procesa el pago enviado por el Card Brick"""
    try:
        data = json.loads(request.body)
        carrito = get_or_create_cart(request)
        
        # Preparar los datos para la API de Mercado Pago
        payment_data = {
            "transaction_amount": float(data.get("transaction_amount")),
            "token": data.get("token"),
            "description": f"Compra en Carlo Magno - Carrito #{carrito.id}",
            "installments": int(data.get("installments")),
            "payment_method_id": data.get("payment_method_id"),
            "issuer_id": data.get("issuer_id"),
            "payer": {
                "email": data.get("payer", {}).get("email"),
                "identification": data.get("payer", {}).get("identification"),
            },
            "external_reference": str(carrito.id),
            "statement_descriptor": "CARLOMAGNO",
        }
        
        mp_service = MercadoPagoService()
        result = mp_service.procesar_pago_tarjeta(payment_data)
        
        # Si el pago fue aprobado
        if result.get("status") == "approved":
            carrito.items.all().delete() # Vaciar el carrito
            return JsonResponse({"success": True})
        else:
            status_detail = result.get("status_detail", "El pago no pudo ser aprobado")
            return JsonResponse({"success": False, "message": status_detail}, status=400)
            
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

def pago_exitoso(request):
    """Vista de retorno para pagos exitosos"""
    carrito = get_or_create_cart(request)
    carrito.items.all().delete() # Vaciar el carrito tras el pago
    return render(request, 'pago_exitoso.html')

def pago_fallido(request):
    """Vista de retorno para pagos fallidos"""
    return render(request, 'pago_fallido.html')

def pago_pendiente(request):
    """Vista de retorno para pagos pendientes"""
    return render(request, 'pago_pendiente.html')
