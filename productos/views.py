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
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    categorias = Categoria.objects.all()
    colores = list(Color.objects.filter(esta_activo=True))
    colores.sort(key=sort_color_rainbow)
    
    talles = Talle.objects.filter(esta_activo=True)
    marcas = Marca.objects.all()
    
    productos = Producto.objects.filter(esta_activo=True).select_related('categoria', 'marca').prefetch_related('colores', 'stock_items')
    
    # Filtrar por categorías (incluyendo subcategorías recursivamente)
    all_cat_ids = set()
    if categoria_ids:
        all_cat_ids = set([int(cid) for cid in categoria_ids if cid.isdigit()])
        # Expandimos para incluir hijos (hasta 3 niveles de profundidad)
        curr_ids = list(all_cat_ids)
        for _ in range(3):
            next_ids = Categoria.objects.filter(parent_id__in=curr_ids).values_list('id', flat=True)
            if not next_ids: break
            all_cat_ids.update(next_ids)
            curr_ids = list(next_ids)
        
        productos = productos.filter(categoria_id__in=all_cat_ids)
    
    # Filtrar por color
    if color_id:
        productos = productos.filter(colores__id=color_id).distinct()
    
    # Filtrar por talle
    if talle_id:
        productos = productos.filter(stock_items__talle_id=talle_id).distinct()
    
    # Filtrar por marca
    if marca_id:
        productos = productos.filter(marca_id=marca_id)

    # Filtrar por precio
    if min_price:
        productos = productos.filter(precio__gte=min_price)
    if max_price:
        productos = productos.filter(precio__lte=max_price)

    # Determinar rango de precios real para el slider
    from django.db.models import Min, Max
    precio_min_db = Producto.objects.filter(esta_activo=True).aggregate(Min('precio'))['precio__min'] or 0
    precio_max_db = Producto.objects.filter(esta_activo=True).aggregate(Max('precio'))['precio__max'] or 0
    
    # Redondear para estética
    precio_min_db = int(precio_min_db)
    precio_max_db = int(precio_max_db)
    
    # Determinar qué colores y talles tienen stock disponible REAL (filtrado por el resto de los filtros)
    base_productos = Producto.objects.filter(esta_activo=True)
    if all_cat_ids:
        base_productos = base_productos.filter(categoria_id__in=all_cat_ids)
    if marca_id:
        base_productos = base_productos.filter(marca_id=marca_id)
    if min_price:
        base_productos = base_productos.filter(precio__gte=min_price)
    if max_price:
        base_productos = base_productos.filter(precio__lte=max_price)
    
    colores_con_stock = Color.objects.filter(productostock__stock__gt=0, productos__in=base_productos).values_list('id', flat=True).distinct()
    talles_con_stock = Talle.objects.filter(productostock__stock__gt=0, productos__in=base_productos).values_list('id', flat=True).distinct()
    
    # Mapeo Maestro UX/UI Premium - Estructura completa y visible
    MASTER_GROUPS = {
        'SUPERIORES': {
            'Camisas': ['camisa'],
            'Remeras': ['remera'],
            'Chombas': ['chomba'],
            'Sweaters & Chalecos': ['sweater', 'polera', 'pullover', 'chaleco']
        },
        'INFERIORES': {
            'Pantalones & Jeans': ['pantalón', 'pantalon', 'gabardina', 'chino', 'lino', 'jean'],
            'Bermudas & Joggers': ['bermuda', 'jogger']
        },
        'SACOS Y ABRIGOS': {
            'Sacos & Blazers': ['saco', 'blazer', 'ambo', 'traje'],
            'Camperas': ['campera', 'pilotin', 'impermeable']
        },
        'ACCESORIOS': {
            'Cintos': ['cinto'],
            'Corbatas & Pañuelos': ['corbata', 'pañuelo', 'pasador', 'pisa corbata'],
            'Gemelos & Complementos': ['mancuernilla', 'gemelos'], # Quitamos 'accesorios' para que no sea tan broad
            'Medias & Ropa Interior': ['media', 'bóxer', 'boxer']
        },
        'REGALOS': {
            'Gift Cards': ['gift card'],
            'Kits & Otros': ['kit', 'regalo']
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
            # Mostramos todas las categorías que coincidan con los keywords, tengan productos o no
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

    # Sección VARIOS: para todo lo que no entró en el mapeo principal
    varios_subgroups = {}
    varios_is_active = False
    for c in categorias:
        if c.id not in mapped_cat_ids and c.nombre.lower() not in ['inicio', 'cat1']:
            varios_subgroups[c.nombre] = [c]
            if c.id in selected_cat_ints:
                varios_is_active = True
    
    if varios_subgroups:
        categorias_grouped_list.append({
            'name': 'VARIOS',
            'subgroups': varios_subgroups,
            'is_active': varios_is_active
        })
    
    # El filtrado de categorías ya se realizó arriba. Eliminamos la duplicación.
    
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
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'precio_min_db': precio_min_db,
        'precio_max_db': precio_max_db,
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