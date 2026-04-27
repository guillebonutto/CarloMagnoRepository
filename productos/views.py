from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria, Color, Talle, Marca

def home(request):
    # Traemos los productos más recientes y activos (Estilo Novedades de Shein)
    novedades = Producto.objects.filter(esta_activo=True).select_related('categoria', 'marca').order_by('-id')[:20]
    categorias_principales = Categoria.objects.all()[:8] # Accesos rápidos
    
    return render(request, 'index.html', {
        'novedades': novedades,
        'categorias_principales': categorias_principales
    })

def producto_list(request):
    categoria_ids = request.GET.getlist('categoria')
    color_id = request.GET.get('color')
    talle_id = request.GET.get('talle')
    marca_id = request.GET.get('marca')
    
    categorias = Categoria.objects.all()
    colores = Color.objects.filter(esta_activo=True)
    talles = Talle.objects.filter(esta_activo=True)
    marcas = Marca.objects.all()
    
    productos = Producto.objects.filter(esta_activo=True).select_related('categoria', 'marca').prefetch_related('colores', 'stock_items').all()
    
    # Filtrar por categorías (múltiples)
    if categoria_ids:
        productos = productos.filter(categoria_id__in=categoria_ids)
    
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
    
    # Mapeo Maestro UX/UI Premium
    MASTER_GROUPS = {
        'SUPERIORES': {
            'Camisas': ['camisas', 'camisas m/c'],
            'Remeras': ['remera', 'remeras'],
            'Chombas & Polos': ['chombas'],
            'Sweaters & Cardigans': ['sweaters', 'polera'],
            'Chalecos': ['chaleco']
        },
        'INFERIORES': {
            'Pantalones': ['pantalón lino', 'gabardina corte chino', 'poplin chino'],
            'Jeans': ['jean'],
            'Bermudas': ['bermudas'],
            'Joggers': ['jogger'],
            'Pantalones 7/8': ['7/8']
        },
        'EXTERIOR': {
            'Camperas': ['campera algodón', 'campera lana', 'campera paño', 'campera impermeable'],
            'Impermeables & Pilotines': ['pilotín', 'pilotin'],
            'Sacos Sport / Blazers': ['saco sport']
        },
        'FORMAL': {
            'Trajes & Ambos': ['ambo'],
            'Corbatas & Pañuelos': ['corbatas']
        },
        'ACCESORIOS': {
            'Cintos': ['cintos'],
            'Medias & Ropa Interior': ['medias', 'bóxers'],
            'Pulseras & Complementos': ['pulsera', 'pulsers']
        }
    }

    # Agrupar categorías reales según el mapeo
    categorias_grouped = {}
    mapped_cat_ids = set()
    
    for group_name, subgroups in MASTER_GROUPS.items():
        categorias_grouped[group_name] = {}
        for subgroup_name, keywords in subgroups.items():
            matching_cats = [c for c in categorias if any(k in c.nombre.lower() for k in keywords)]
            if matching_cats:
                categorias_grouped[group_name][subgroup_name] = matching_cats
                for c in matching_cats:
                    mapped_cat_ids.add(c.id)

    # Añadir sección OTROS para lo que no encajó (para evitar que se pierdan productos)
    otros_cats = [c for c in categorias if c.id not in mapped_cat_ids and c.nombre.lower() not in ['inicio', 'cat1']]
    if otros_cats:
        categorias_grouped['VARIOS'] = {'Otros Complementos': otros_cats}
    
    # Filtrar por categorías (múltiples)
    if categoria_ids:
        productos = productos.filter(categoria_id__in=categoria_ids)
    
    return render(request, 'producto.html', {
        'productos': productos,
        'categorias_grouped': categorias_grouped,
        'colores': colores,
        'talles': talles,
        'marcas': marcas,
        'selected_categorias': categoria_ids,
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
