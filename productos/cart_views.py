# Crear archivo: productos/cart_views.py

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
        
        # Verificar stock
        try:
            stock = ProductoStock.objects.get(
                producto=producto,
                color=color,
                talle=talle
            )
            if stock.stock < cantidad:
                return JsonResponse({
                    'success': False,
                    'message': f'Solo hay {stock.stock} unidades disponibles'
                }, status=400)
        except ProductoStock.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No hay stock disponible para esta combinación'
            }, status=400)
        
        # Obtener o crear carrito
        carrito = get_or_create_cart(request)
        
        # Agregar o actualizar item
        item, created = CarritoItem.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            color=color,
            talle=talle,
            defaults={'cantidad': cantidad}
        )
        
        if not created:
            nueva_cantidad = item.cantidad + cantidad
            if nueva_cantidad > stock.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Solo puedes agregar {stock.stock - item.cantidad} unidades más'
                }, status=400)
            item.cantidad = nueva_cantidad
            item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito',
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
def eliminar_del_carrito(request):
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
    
    messages.success(request, 'Carrito vaciado correctamente')
    return redirect('inicio')