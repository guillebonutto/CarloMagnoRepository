from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria, Color, Talle, Marca
import colorsys
def sort_color_rainbow(color):
    """
    Orden lógico premium para filtros de color en indumentaria masculina.
    """
    try:
        hex_code = str(color.hex_code).lstrip('#').upper()
        if len(hex_code) == 3:
            hex_code = ''.join(c * 2 for c in hex_code)

        r = int(hex_code[0:2], 16) / 255.0
        g = int(hex_code[2:4], 16) / 255.0
        b = int(hex_code[4:6], 16) / 255.0

        h, l, s = colorsys.rgb_to_hls(r, g, b)

        # Neutros (blanco, beige, grises)
        is_neutral = (s < 0.18) or (l < 0.15) or (l > 0.87)

        if is_neutral:
            if l > 0.58:      # Blancos y claros
                return (0, -l, 0)           # Grupo 0: Neutros Claros
            else:             # Grises y Negro
                return (5, -l, 0)           # Grupo 5: Neutros Oscuros (al final)

        # ====================== COLORES CROMÁTICOS ======================
        # Orden: Cálidos → Verdes → Celeste → Azul

        if h < 0.085 or h > 0.92:           # Rojo / Bordo
            hue_group = 1
        elif h < 0.20:                      # Naranja / Amarillo / Camel
            hue_group = 2
        elif h < 0.45:                      # Verdes (incluido Verde Militar)
            hue_group = 3
        elif h < 0.60:                      # CELESTE ← Aquí lo forzamos
            hue_group = 4
        elif h < 0.80:                      # Azul
            hue_group = 5
        else:                               # Rosa fuerte / Violeta
            hue_group = 6

        return (2, hue_group, -l)   # Grupo 2 = Colores cromáticos

    except Exception:
        return (6, 0, 0)


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
    colores = list(Color.objects.filter(esta_activo=True))
    colores.sort(key=sort_color_rainbow)
    
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
    categorias_grouped_list = []
    mapped_cat_ids = set()
    
    # Convertir categoria_ids a enteros para comparar fácilmente
    selected_cat_ints = [int(cid) for cid in categoria_ids if cid.isdigit()]
    
    for group_name, subgroups in MASTER_GROUPS.items():
        group_subgroups = {}
        group_is_active = False
        
        for subgroup_name, keywords in subgroups.items():
            matching_cats = [c for c in categorias if any(k in c.nombre.lower() for k in keywords)]
            if matching_cats:
                group_subgroups[subgroup_name] = matching_cats
                if any(c.id in selected_cat_ints for c in matching_cats):
                    group_is_active = True
                for c in matching_cats:
                    mapped_cat_ids.add(c.id)
        
        if group_subgroups:
            categorias_grouped_list.append({
                'name': group_name,
                'subgroups': group_subgroups,
                'is_active': group_is_active
            })

    # Añadir sección VARIOS para lo que no encajó
    otros_cats = [c for c in categorias if c.id not in mapped_cat_ids and c.nombre.lower() not in ['inicio', 'cat1']]
    if otros_cats:
        is_otros_active = any(c.id in selected_cat_ints for c in otros_cats)
        categorias_grouped_list.append({
            'name': 'VARIOS',
            'subgroups': {'Otros Complementos': otros_cats},
            'is_active': is_otros_active
        })
    
    # Filtrar por categorías (múltiples)
    if categoria_ids:
        productos = productos.filter(categoria_id__in=categoria_ids)
    
    return render(request, 'producto.html', {
        'productos': productos,
        'categorias_grouped': categorias_grouped_list,
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
    
    # Obtener colores y talles disponibles y ordenar con la función mejorada
    colores_disponibles = list(Color.objects.filter(productostock__producto=producto).distinct())
    colores_disponibles.sort(key=sort_color_rainbow)
    
    talles_disponibles = Talle.objects.filter(productostock__producto=producto).distinct()
    
    return render(request, 'producto_detail.html', {
        'producto': producto,
        'stock_items': stock_items,
        'colores_disponibles': colores_disponibles,
        'talles_disponibles': talles_disponibles,
    })