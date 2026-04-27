from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria, Color, Talle, Marca

def home(request):
    featured_productos = Producto.objects.select_related('categoria', 'marca').prefetch_related('colores').all()[:6]
    return render(request, 'index.html', {
        'featured_productos': featured_productos
    })

def producto_list(request):
    categoria_id = request.GET.get('categoria')
    color_id = request.GET.get('color')
    talle_id = request.GET.get('talle')
    marca_id = request.GET.get('marca')
    
    categorias = Categoria.objects.all()
    colores = Color.objects.filter(esta_activo=True)
    talles = Talle.objects.filter(esta_activo=True)
    marcas = Marca.objects.all()
    
    productos = Producto.objects.select_related('categoria', 'marca').prefetch_related('colores', 'stock_items').all()
    
    # Filtrar por categoría
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    # Filtrar por color
    if color_id:
        productos = productos.filter(colores__id=color_id).distinct()
    
    # Filtrar por talle
    if talle_id:
        productos = productos.filter(stock_items__talle_id=talle_id).distinct()
    
    # Filtrar por marca
    if marca_id:
        productos = productos.filter(marca_id=marca_id)
    
    # Determinar qué colores y talles tienen stock disponible (en general o según filtros)
    colores_con_stock = Color.objects.filter(productostock__stock__gt=0).values_list('id', flat=True).distinct()
    talles_con_stock = Talle.objects.filter(productostock__stock__gt=0).values_list('id', flat=True).distinct()
    
    return render(request, 'producto.html', {
        'productos': productos,
        'categorias': categorias,
        'colores': colores,
        'talles': talles,
        'marcas': marcas,
        'selected_categoria': categoria_id,
        'selected_color': color_id,
        'selected_talle': talle_id,
        'selected_marca': marca_id,
        'colores_con_stock': list(colores_con_stock),
        'talles_con_stock': list(talles_con_stock),
    })

def producto_detail(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'marca').prefetch_related('colores', 'stock_items'),
        id=producto_id
    )
    stock_items = producto.stock_items.select_related('color', 'talle').filter(stock__gt=0)
    
    # Obtener colores y talles disponibles
    colores_disponibles = Color.objects.filter(productostock__producto=producto).distinct()
    talles_disponibles = Talle.objects.filter(productostock__producto=producto).distinct()
    
    return render(request, 'producto_detail.html', {
        'producto': producto,
        'stock_items': stock_items,
        'colores_disponibles': colores_disponibles,
        'talles_disponibles': talles_disponibles,
    })
