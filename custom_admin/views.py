from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as django_login, authenticate
from django.contrib.auth import logout as django_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.forms import ModelForm
from django import forms
from productos.models import Producto, Categoria, Color, Estilo, Tipo, Marca, Talle, Cliente, Direccion, ProductoStock, Pedido, PedidoItem, Cupon, Carrito, CarritoItem, MetaMensual, RegistroVisita
from productos.forms import ProductoForm, IngresoStockPorLectorForm
from django.db import router, transaction
from django.db.models import F, Q, Sum, Count, Avg
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from datetime import timedelta
import unicodedata
import json
import math

# Formularios
# class ProductForm(ModelForm):
#     class Meta:
#         model = Producto
#         fields = ['nombre', 'descripcion', 'precio', 'categoria', 'marca', 'talle', 'colores', 'imagen']
#         widgets = {
#             'colores': forms.CheckboxSelectMultiple(),
#         }

class CategoryForm(ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'parent', 'descripcion']

class ColorForm(ModelForm):
    class Meta:
        model = Color
        fields = ['nombre', 'hex_code', 'order']

class MarcaForm(ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre', 'logo', 'website', 'descripcion']

class TalleForm(ModelForm):
    class Meta:
        model = Talle
        fields = ['abbreviation', 'nombre', 'order']

class EstiloForm(ModelForm):
    class Meta:
        model = Estilo
        fields = ['nombre', 'order', 'esta_activo']

class TipoForm(ModelForm):
    class Meta:
        model = Tipo
        fields = ['nombre', 'order', 'esta_activo']

class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'tratamiento',
            'nombre',
            'apellidos',
            'email',
            'grupo',
            'ventas_totales',
            'activado',
            'boletin',
            'ofertas_asociados',
            'ultima_visita'
        ]
        widgets = {
            'fecha_registro': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ultima_visita': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class DireccionForm(ModelForm):
    class Meta:
        model = Direccion
        fields = [
            'cliente',
            'nombre',
            'apellidos',
            'direccion',
            'codigo_postal',
            'ciudad',
            'pais',
            'telefono',
            'es_predeterminada'
        ]

class StockForm(ModelForm):
    class Meta:
        model = ProductoStock
        fields = ['producto', 'color', 'talle', 'stock']


class StockQuantityForm(forms.Form):
    stock = forms.IntegerField(
        min_value=0,
        label='Cantidad de stock',
        widget=forms.NumberInput(attrs={'min': 0, 'step': 1}),
    )


class StockBarcodeForm(forms.Form):
    codigo = forms.CharField(
        max_length=50,
        strip=True,
        label='Código del artículo',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'off',
            'placeholder': 'Escaneá el código del artículo',
            'data-stock-barcode': '',
        }),
    )


# Vista de login
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            django_login(request, user)  # 🔹 usamos la función de Django, no la vista
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('dashboard')
        else:
            return render(request, 'custom_admin/login.html', {'error': 'Credenciales inválidas'})
    
    return render(request, 'custom_admin/login.html')

# Vista de logout
def cerrar_sesion(request):
    django_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login')

@login_required(login_url='login')
def cambiar_contrasena(request):
    if not request.user.is_staff:
        return redirect('inicio')

    form = PasswordChangeForm(
        user=request.user,
        data=request.POST if request.method == 'POST' else None,
    )
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Tu contraseña se actualizó correctamente.')
        return redirect('cambiar_contrasena')

    return render(request, 'custom_admin/cambiar_contrasena.html', {'form': form})

# Dashboard estilo PrestaShop
@login_required(login_url='login')
def dashboard(request):
    if not request.user.is_staff:
        return redirect('inicio')
    
    # Manejar Demo Mode (activable vía GET ?demo=1 o por defecto si aún no hay pedidos cargados)
    demo_param = request.GET.get('demo')
    total_pedidos_reales = Pedido.objects.count()
    demo_mode = (demo_param == '1') or (demo_param is None and total_pedidos_reales == 0)
    if demo_param == '0':
        demo_mode = False

    # Filtro de Período
    periodo = request.GET.get('periodo', 'year')
    now = timezone.now()
    hoy = now.date()
    
    # Calcular rangos de fechas según período
    if periodo == 'day':
        fecha_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        fecha_inicio_ant = fecha_inicio - timedelta(days=1)
        fecha_fin_ant = fecha_fin - timedelta(days=1)
        label_periodo = "Hoy"
    elif periodo == 'month':
        fecha_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        primer_dia_este_mes = fecha_inicio
        ultimo_dia_mes_ant = primer_dia_este_mes - timedelta(days=1)
        fecha_inicio_ant = ultimo_dia_mes_ant.replace(day=1)
        fecha_fin_ant = ultimo_dia_mes_ant
        label_periodo = "Este Mes"
    elif periodo == 'day-1':
        fecha_inicio = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59)
        fecha_inicio_ant = fecha_inicio - timedelta(days=1)
        fecha_fin_ant = fecha_fin - timedelta(days=1)
        label_periodo = "Ayer"
    elif periodo == 'month-1':
        primer_dia_este_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ultimo_dia_mes_ant = primer_dia_este_mes - timedelta(days=1)
        fecha_inicio = ultimo_dia_mes_ant.replace(day=1)
        fecha_fin = ultimo_dia_mes_ant
        fecha_inicio_ant = (fecha_inicio - timedelta(days=1)).replace(day=1)
        fecha_fin_ant = fecha_inicio - timedelta(days=1)
        label_periodo = "Mes Anterior"
    elif periodo == 'year-1':
        fecha_inicio = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59)
        fecha_inicio_ant = fecha_inicio.replace(year=now.year - 2)
        fecha_fin_ant = fecha_fin.replace(year=now.year - 2)
        label_periodo = f"Año {now.year - 1}"
    else: # 'year' por defecto
        fecha_inicio = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = now
        fecha_inicio_ant = fecha_inicio.replace(year=now.year - 1)
        fecha_fin_ant = fecha_fin.replace(year=now.year - 1)
        label_periodo = f"Año {now.year}"
        periodo = 'year'

    # 1. Activity Overview (Métricas en tiempo real)
    hace_30_min = now - timedelta(minutes=30)
    carritos_activos = Carrito.objects.filter(actualizado__gte=hace_30_min).count()
    pedidos_pendientes = Pedido.objects.filter(estado_pago='pendiente').count()
    devoluciones = 0
    hace_2_horas = now - timedelta(hours=2)
    carritos_abandonados = Carrito.objects.filter(actualizado__lt=hace_2_horas, items__isnull=False).distinct().count()
    productos_sin_stock = ProductoStock.objects.filter(stock=0).count()
    nuevos_clientes = Cliente.objects.filter(fecha_registro__gte=fecha_inicio.date()).count()
    nuevos_suscriptores = Cliente.objects.filter(boletin=True, fecha_registro__gte=fecha_inicio.date()).count()
    total_suscriptores = Cliente.objects.filter(boletin=True).count()

    # Si está en demo_mode y no hay carritos/datos, asegurar números para la vista previa
    if demo_mode:
        if carritos_activos == 0: carritos_activos = 2
        if pedidos_pendientes == 0: pedidos_pendientes = 2
        if devoluciones == 0: devoluciones = 1
        if carritos_abandonados == 0: carritos_abandonados = 15
        if productos_sin_stock == 0: productos_sin_stock = 2
        nuevos_mensajes = 588
        reviews_count = 6319
        if nuevos_clientes == 0: nuevos_clientes = 735
        if nuevos_suscriptores == 0: nuevos_suscriptores = 294
        if total_suscriptores == 0: total_suscriptores = 1174
    else:
        nuevos_mensajes = 0
        reviews_count = 0

    # 2. Métricas del Dashboard (KPIs)
    pedidos_periodo = Pedido.objects.filter(estado_pago='pagado', fecha_creacion__gte=fecha_inicio, fecha_creacion__lte=fecha_fin)
    pedidos_ant = Pedido.objects.filter(estado_pago='pagado', fecha_creacion__gte=fecha_inicio_ant, fecha_creacion__lte=fecha_fin_ant)

    ventas_reales = pedidos_periodo.aggregate(Sum('total'))['total__sum'] or 0
    ventas_ant = pedidos_ant.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_pedidos = pedidos_periodo.count()
    cantidad_pedidos_ant = pedidos_ant.count()

    # Visitas
    visitas_periodo = RegistroVisita.objects.filter(fecha__gte=fecha_inicio.date(), fecha__lte=fecha_fin.date()).aggregate(Sum('visitas'))['visitas__sum'] or 0

    if demo_mode and ventas_reales == 0:
        ventas_display = 3500506.00
        ventas_diff = 2.72
        pedidos_display = 27878
        pedidos_diff = 6.32
        ticket_display = 125.57
        ticket_diff = -3.39
        visitas_display = 1703602
        visitas_diff = 7.69
        conversion_display = 1.64
        conversion_diff = -0.02
        beneficio_display = 1209348.15
        beneficio_diff = 0.57
    else:
        ventas_display = float(ventas_reales)
        ventas_diff = round(((float(ventas_reales) - float(ventas_ant)) / float(ventas_ant) * 100) if ventas_ant > 0 else 0, 2)
        pedidos_display = cantidad_pedidos
        pedidos_diff = round(((cantidad_pedidos - cantidad_pedidos_ant) / cantidad_pedidos_ant * 100) if cantidad_pedidos_ant > 0 else 0, 2)
        ticket_display = round(ventas_display / pedidos_display, 2) if pedidos_display > 0 else 0
        ticket_diff = 0.0
        visitas_display = visitas_periodo if visitas_periodo > 0 else (pedidos_display * 30)
        visitas_diff = 0.0
        conversion_display = round((pedidos_display / visitas_display * 100), 2) if visitas_display > 0 else 0.0
        conversion_diff = 0.0
        beneficio_display = round(ventas_display * 0.35, 2)
        beneficio_diff = ventas_diff

    # 3. Datos para el Gráfico Forecast (Mes a Mes)
    meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    # Obtener metas mensuales o usar estimación de previsión
    metas_dict = {m.mes: m for m in MetaMensual.objects.filter(año=now.year)}
    if demo_mode and not metas_dict and ventas_reales == 0:
        forecast_sales_actual = [120000, 150000, 180000, 220000, 260000, 290000, 340000, 390000, 430000, 480000, 520000, 580000]
        forecast_sales_target = [140000, 170000, 200000, 240000, 280000, 310000, 360000, 410000, 460000, 510000, 550000, 620000]
        forecast_traffic = [24000, 28000, 31000, 35000, 39000, 42000, 47000, 51000, 56000, 61000, 65000, 72000]
        forecast_orders = [1200, 1450, 1700, 1950, 2200, 2450, 2800, 3100, 3400, 3750, 4100, 4600]
    else:
        forecast_sales_actual = []
        forecast_sales_target = []
        forecast_traffic = []
        forecast_orders = []
        for m in range(1, 13):
            v_mes = Pedido.objects.filter(estado_pago='pagado', fecha_creacion__year=now.year, fecha_creacion__month=m).aggregate(Sum('total'))['total__sum'] or 0
            p_mes = Pedido.objects.filter(estado_pago='pagado', fecha_creacion__year=now.year, fecha_creacion__month=m).count()
            meta = metas_dict.get(m)
            target = float(meta.meta_ventas) if meta else (float(v_mes) * 1.2 if v_mes > 0 else 100000.0)
            forecast_sales_actual.append(float(v_mes))
            forecast_sales_target.append(target)
            forecast_orders.append(p_mes)
            forecast_traffic.append(p_mes * 30)

    # 4. Datos para el Gráfico de Tendencias (Líneas comparativas PrestaShop)
    if demo_mode and ventas_reales == 0:
        dias_muestras = 30
        trend_labels = [f"Día {i}" for i in range(1, dias_muestras + 1)]
        trend_sales = [round(35000 + 18000 * math.sin(i / 2.5) + (i * 1100), 2) for i in range(1, dias_muestras + 1)]
        trend_sales_prev = [round(28000 + 14000 * math.sin(i / 2.7) + (i * 850), 2) for i in range(1, dias_muestras + 1)]
    else:
        dias_muestras = 30
        trend_labels = [f"Día {i}" for i in range(1, dias_muestras + 1)]
        trend_sales = [0] * dias_muestras
        trend_sales_prev = [0] * dias_muestras

    # Estaciones (para compatibilidad de métricas existentes)
    estaciones = {'Verano': 0, 'Otoño': 0, 'Invierno': 0, 'Primavera': 0}
    for p in Pedido.objects.filter(estado_pago='pagado'):
        estacion = p.get_estacion()
        estaciones[estacion] += float(p.total)

    context = {
        'demo_mode': demo_mode,
        'periodo': periodo,
        'label_periodo': label_periodo,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'año_actual': now.year,

        # Activity overview
        'carritos_activos': carritos_activos,
        'pedidos_pendientes': pedidos_pendientes,
        'devoluciones': devoluciones,
        'carritos_abandonados': carritos_abandonados,
        'productos_sin_stock': productos_sin_stock,
        'nuevos_mensajes': nuevos_mensajes,
        'reviews_count': reviews_count,
        'nuevos_clientes': nuevos_clientes,
        'nuevos_suscriptores': nuevos_suscriptores,
        'total_suscriptores': total_suscriptores,

        # KPIs
        'ventas_display': ventas_display,
        'ventas_diff': ventas_diff,
        'pedidos_display': pedidos_display,
        'pedidos_diff': pedidos_diff,
        'ticket_display': ticket_display,
        'ticket_diff': ticket_diff,
        'visitas_display': visitas_display,
        'visitas_diff': visitas_diff,
        'conversion_display': conversion_display,
        'conversion_diff': conversion_diff,
        'beneficio_display': beneficio_display,
        'beneficio_diff': beneficio_diff,

        # Gráficos (JSON para Chart.js)
        'meses_nombres_json': json.dumps(meses_nombres),
        'forecast_sales_actual_json': json.dumps(forecast_sales_actual),
        'forecast_sales_target_json': json.dumps(forecast_sales_target),
        'forecast_traffic_json': json.dumps(forecast_traffic),
        'forecast_orders_json': json.dumps(forecast_orders),
        'trend_labels_json': json.dumps(trend_labels),
        'trend_sales_json': json.dumps(trend_sales),
        'trend_sales_prev_json': json.dumps(trend_sales_prev),

        # Totales generales catálogo
        'total_productos': Producto.objects.count(),
        'total_categories': Categoria.objects.count(),
        'total_marcas': Marca.objects.count(),
        'low_stock': ProductoStock.objects.filter(stock__lt=5).count(),
        'pedidos_con_cupon': Pedido.objects.filter(estado_pago='pagado', cupon__isnull=False).count(),
        'recent_pedidos': Pedido.objects.order_by('-fecha_creacion')[:8],
    }
    return render(request, 'custom_admin/dashboard.html', context)


# Gestión de productos
@login_required(login_url='login')
def productos(request):
    if not request.user.is_staff:
        return redirect('home')
    
    # Obtener parámetros de filtrado y ordenamiento
    sort_by = request.GET.get('sort', 'nombre')
    direction = request.GET.get('direction', 'asc')
    cat_filter = request.GET.get('categoria')
    marca_filter = request.GET.get('marca')
    search_query = request.GET.get('buscar', '').strip()
    
    # Queryset base
    productos_qs = Producto.objects.select_related('categoria', 'marca').all()
    
    # Aplicar filtros
    if search_query:
        productos_qs = productos_qs.filter(
            Q(codigo__icontains=search_query)
            | Q(nombre__icontains=search_query)
        )
    if cat_filter and cat_filter.isdigit():
        categoria_ids = {int(cat_filter)}
        pendientes = list(categoria_ids)
        while pendientes:
            subcategorias = set(
                Categoria.objects.filter(parent_id__in=pendientes)
                .values_list('id', flat=True)
            ) - categoria_ids
            categoria_ids.update(subcategorias)
            pendientes = list(subcategorias)
        productos_qs = productos_qs.filter(categoria_id__in=categoria_ids)
    if marca_filter and marca_filter.isdigit():
        productos_qs = productos_qs.filter(marca_id=marca_filter)
    
    # Mapeo de campos para evitar inyección o errores
    sort_map = {
        'nombre': 'nombre',
        'precio': 'precio',
        'categoria': 'categoria__nombre',
        'marca': 'marca__nombre',
        'fecha': 'created_at'
    }
    
    db_field = sort_map.get(sort_by, 'nombre')
    if direction == 'desc':
        db_field = f'-{db_field}'
        
    productos_qs = productos_qs.order_by(db_field)
    
    context = {
        'productos': productos_qs,
        'categorias': Categoria.objects.all().order_by('parent__nombre', 'nombre'),
        'marcas': Marca.objects.all(),
        'current_sort': sort_by,
        'current_direction': direction,
        'current_cat': cat_filter,
        'current_marca': marca_filter,
        'search_query': search_query,
    }
    
    return render(request, 'custom_admin/productos.html', context)

@login_required(login_url='login')
def agregar_producto(request):
    if not request.user.is_staff:
        return redirect('inicio')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Producto creado exitosamente')
            return redirect('admin_productos')
        else:
            messages.error(request, '❌ Error al crear el producto. Por favor revisa los datos ingresados.')
    else:
        form = ProductoForm()
    
    return render(request, 'custom_admin/producto_form.html', {
        'form': form,
        'title': 'Agregar Producto',
        'button_text': 'Agregar Producto'
    })

@login_required(login_url='login')
def editar_producto(request, pk):
    if not request.user.is_staff:
        return redirect('inicio')
    
    product = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Producto actualizado exitosamente')
            return redirect('admin_productos')
        else:
            messages.error(request, '❌ Error al actualizar el producto. Por favor revisa los datos ingresados.')
    else:
        form = ProductoForm(instance=product)
    
    return render(request, 'custom_admin/producto_form.html', {
        'form': form,
        'title': 'Editar Producto',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_producto(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        producto.delete()
        messages.success(request, '✅ Producto eliminado exitosamente')
        return redirect('admin_productos')
    
    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': producto,
        'type': 'producto'
    })

@login_required(login_url='login')
@require_POST
def toggle_producto_status(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    producto = get_object_or_404(Producto, pk=pk)
    producto.esta_activo = not producto.esta_activo
    producto.save()
    
    return JsonResponse({
        'status': 'success',
        'is_active': producto.esta_activo
    })

def _get_category_tree():
    categories = list(
        Categoria.objects.annotate(productos_directos=Count('productos'))
        .order_by('nombre')
    )
    children_by_parent = {}
    for category in categories:
        category.children = []
        category.productos_totales = category.productos_directos
        if category.parent_id is not None:
            children_by_parent.setdefault(category.parent_id, []).append(category)

    def count_subtree(category, ancestors=frozenset()):
        if category.pk in ancestors:
            raise ValueError('Se encontró un ciclo en la jerarquía de categorías.')
        descendants = ancestors | {category.pk}
        category.children = children_by_parent.get(category.pk, [])
        category.productos_totales = category.productos_directos + sum(
            count_subtree(child, descendants)
            for child in category.children
        )
        return category.productos_totales

    root_categories = [
        category for category in categories if category.parent_id is None
    ]
    for category in root_categories:
        count_subtree(category)

    return root_categories


# Gestión de categorías
@login_required(login_url='login')
def categorias(request):
    if not request.user.is_staff:
        return redirect('home')

    return render(
        request,
        'custom_admin/categorias.html',
        {'categories': _get_category_tree()},
    )


@login_required(login_url='login')
def detalle_categoria(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    categoria = get_object_or_404(Categoria, pk=pk, parent__isnull=True)
    categoria = next(
        category
        for category in _get_category_tree()
        if category.pk == categoria.pk
    )
    categoria_ids = {categoria.pk}
    pendientes = list(categoria.children)
    while pendientes:
        subcategoria = pendientes.pop()
        if subcategoria.pk in categoria_ids:
            continue
        categoria_ids.add(subcategoria.pk)
        pendientes.extend(subcategoria.children)

    productos_categoria = list(
        Producto.objects.filter(categoria_id__in=categoria_ids)
        .select_related('categoria', 'marca')
        .order_by('nombre')
    )
    productos_por_categoria = {}
    for producto in productos_categoria:
        productos_por_categoria.setdefault(producto.categoria_id, []).append(producto)

    product_groups = []

    def agrupar_productos(category, ancestors=()):
        category_path = (*ancestors, category.nombre)
        productos_directos = productos_por_categoria.get(category.pk, [])
        if productos_directos:
            product_groups.append({
                'nombre': ' / '.join(category_path),
                'productos': productos_directos,
            })
        for child in category.children:
            agrupar_productos(child, category_path)

    agrupar_productos(categoria)

    return render(
        request,
        'custom_admin/categoria_detalle.html',
        {
            'categoria': categoria,
            'productos': productos_categoria,
            'product_groups': product_groups,
        },
    )


@login_required(login_url='login')
def agregar_categoria(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Categoría creada exitosamente')
            return redirect('categorias')
    else:
        form = CategoryForm()
    
    return render(request, 'custom_admin/categoria_form.html', {
        'form': form,
        'title': 'Agregar Categoría',
        'button_text': 'Agregar Categoría'
    })

@login_required(login_url='login')
def editar_categoria(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Categoría actualizada exitosamente')
            return redirect('categorias')
    else:
        form = CategoryForm(instance=categoria)
    
    return render(request, 'custom_admin/categoria_form.html', {
        'form': form,
        'title': 'Editar Categoría',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_categoria(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, '✅ Categoría eliminada exitosamente')
        return redirect('categorias')
    
    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': categoria,
        'type': 'categoría'
    })

# Gestión de colores
@login_required(login_url='login')
def colores(request):
    if not request.user.is_staff:
        return redirect('home')
    
    colores = Color.objects.all()
    return render(request, 'custom_admin/colores.html', {'colores': colores})

@login_required(login_url='login')
def agregar_color(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Color creado exitosamente')
            return redirect('colores')
    else:
        form = ColorForm()
    
    return render(request, 'custom_admin/color_form.html', {
        'form': form,
        'title': 'Agregar Color',
        'button_text': 'Agregar Color'
    })

@login_required(login_url='login')
def editar_color(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    color = get_object_or_404(Color, pk=pk)
    
    if request.method == 'POST':
        form = ColorForm(request.POST, request.FILES, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Color actualizado exitosamente')
            return redirect('colores')
    else:
        form = ColorForm(instance=color)
    
    return render(request, 'custom_admin/color_form.html', {
        'form': form,
        'title': 'Editar Color',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_color(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    color = get_object_or_404(Color, pk=pk)
    
    if request.method == 'POST':
        color.delete()
        messages.success(request, '✅ Color eliminado exitosamente')
        return redirect('colores')
    
    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': color,
        'type': 'color'
    })
# Gestión de marcas
@login_required(login_url='login')
def marcas(request):
    if not request.user.is_staff:
        return redirect('home')
    
    marcas = Marca.objects.all()
    return render(request, 'custom_admin/marcas.html', {'marcas': marcas})

@login_required(login_url='login')
def agregar_marca(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = MarcaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Marca creada exitosamente')
            return redirect('marcas')
    else:
        form = MarcaForm()
    
    return render(request, 'custom_admin/marca_form.html', {
        'form': form,
        'title': 'Agregar Marca',
        'button_text': 'Agregar Marca'
    })

@login_required(login_url='login')
def editar_marca(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    color = get_object_or_404(Marca, pk=pk)
    
    if request.method == 'POST':
        form = MarcaForm(request.POST, request.FILES, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Marca actualizada exitosamente')
            return redirect('marcas')
    else:
        form = MarcaForm(instance=color)
    
    return render(request, 'custom_admin/marca_form.html', {
        'form': form,
        'title': 'Editar Marca',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_marca(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    marca = get_object_or_404(Marca, pk=pk)
    
    if request.method == 'POST':
        Marca.delete()
        messages.success(request, '✅ Marca eliminada exitosamente')
        return redirect('marcas')
    
    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': marca,
        'type': 'marca'
    })

# Gestión de Talles
@login_required(login_url='login')
def talles(request):
    if not request.user.is_staff:
        return redirect('home')
    
    talles = Talle.objects.all()
    return render(request, 'custom_admin/talles.html', {'talles': talles})

@login_required(login_url='login')
def agregar_talle(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = TalleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Talle creado exitosamente')
            return redirect('talles')
    else:
        form = TalleForm()
    
    return render(request, 'custom_admin/talle_form.html', {
        'form': form,
        'title': 'Agregar Talle',
        'button_text': 'Agregar Talle'
    })

@login_required(login_url='login')
def editar_talle(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    color = get_object_or_404(Talle, pk=pk)
    
    if request.method == 'POST':
        form = TalleForm(request.POST, request.FILES, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Talle actualizada exitosamente')
            return redirect('marcas')
    else:
        form = TalleForm(instance=color)
    
    return render(request, 'custom_admin/talle_form.html', {
        'form': form,
        'title': 'Editar Marca',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_talle(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    talle = get_object_or_404(Talle, pk=pk)
    
    if request.method == 'POST':
        Talle.delete()
        messages.success(request, '✅ Talle eliminada exitosamente')
        return redirect('talles')
    
    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': talle,
        'type': 'talle'
    })


@login_required(login_url='login')
def estilos(request):
    if not request.user.is_staff:
        return redirect('home')

    style_options = Estilo.objects.annotate(productos_count=Count('productos'))
    return render(request, 'custom_admin/estilos.html', {
        'estilos': style_options,
    })


@login_required(login_url='login')
def agregar_estilo(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        form = EstiloForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estilo creado exitosamente')
            return redirect('estilos')
    else:
        form = EstiloForm()

    return render(request, 'custom_admin/estilo_form.html', {
        'form': form,
        'title': 'Agregar estilo',
    })


@login_required(login_url='login')
def editar_estilo(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    estilo = get_object_or_404(Estilo, pk=pk)
    if request.method == 'POST':
        form = EstiloForm(request.POST, instance=estilo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estilo actualizado exitosamente')
            return redirect('estilos')
    else:
        form = EstiloForm(instance=estilo)

    return render(request, 'custom_admin/estilo_form.html', {
        'form': form,
        'title': 'Editar estilo',
    })


@login_required(login_url='login')
def eliminar_estilo(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    estilo = get_object_or_404(Estilo, pk=pk)
    if request.method == 'POST':
        estilo.delete()
        messages.success(request, 'Estilo eliminado exitosamente')
        return redirect('estilos')

    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': estilo,
        'type': 'estilo',
    })


@login_required(login_url='login')
def tipos(request):
    if not request.user.is_staff:
        return redirect('home')

    fabric_types = Tipo.objects.annotate(productos_count=Count('productos'))
    return render(request, 'custom_admin/tipos.html', {
        'tipos': fabric_types,
    })


@login_required(login_url='login')
def agregar_tipo(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        form = TipoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de tela creado exitosamente')
            return redirect('tipos')
    else:
        form = TipoForm()

    return render(request, 'custom_admin/tipo_form.html', {
        'form': form,
        'title': 'Agregar tipo de tela',
    })


@login_required(login_url='login')
def editar_tipo(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    tipo = get_object_or_404(Tipo, pk=pk)
    if request.method == 'POST':
        form = TipoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de tela actualizado exitosamente')
            return redirect('tipos')
    else:
        form = TipoForm(instance=tipo)

    return render(request, 'custom_admin/tipo_form.html', {
        'form': form,
        'title': 'Editar tipo de tela',
    })


@login_required(login_url='login')
def eliminar_tipo(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    tipo = get_object_or_404(Tipo, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de tela eliminado exitosamente')
        return redirect('tipos')

    return render(request, 'custom_admin/confirm_eliminar.html', {
        'object': tipo,
        'type': 'tipo de tela',
    })


@login_required(login_url='login')
def clientes(request):
    if not request.user.is_staff:
        return redirect('home')
    
    clientes = Cliente.objects.all()
    return render(request, 'custom_admin/clientes.html', {'clientes': clientes})

@login_required(login_url='login')
def agregar_cliente(request):
    if not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cliente creado exitosamente')
            return redirect('clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'custom_admin/cliente_form.html', {
        'form': form,
        'title': 'Agregar Cliente',
        'button_text': 'Agregar Cliente'
    })

@login_required(login_url='login')
def editar_cliente(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cliente actualizada exitosamente')
            return redirect('marcas')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'custom_admin/cliente_form.html', {
        'form': form,
        'title': 'Editar Cliente',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_cliente(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        Cliente.delete()
        messages.success(request, '✅ Cliente eliminada exitosamente')
        return redirect('clientes')
    
    return render(request, 'custom_admin/confirmar_eliminar.html', {
        'object': cliente,
        'type': 'cliente'
    })

@login_required(login_url='login')
def direcciones(request):
    if not request.user.is_staff:
        return redirect('inicio')
    
    direcciones = Direccion.objects.all()
    return render(request, 'custom_admin/direcciones.html', {'direcciones': direcciones})

@login_required(login_url='login')
def agregar_direccion(request):
    if not request.user.is_staff:
        return redirect('inicio')
    
    if request.method == 'POST':
        form = DireccionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Direccion añadida exitosamente')
            return redirect('direcciones')
    else:
        form = DireccionForm()
    
    return render(request, 'custom_admin/direccion_form.html', {
        'form': form,
        'title': 'Agregar Dirección',
        'button_text': 'Agregar Dirección'
    })

@login_required(login_url='login')
def editar_direccion(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    color = get_object_or_404(Direccion, pk=pk)
    
    if request.method == 'POST':
        form = DireccionForm(request.POST, request.FILES, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Talle actualizada exitosamente')
            return redirect('direcciones')
    else:
        form = DireccionForm(instance=color)
    
    return render(request, 'custom_admin/direccion_form.html', {
        'form': form,
        'title': 'Editar Dirección',
        'button_text': 'Guardar Cambios'
    })

@login_required(login_url='login')
def eliminar_direccion(request, pk):
    if not request.user.is_staff:
        return redirect('home')
    
    direccion = get_object_or_404(Direccion, pk=pk)
    
    if request.method == 'POST':
        Direccion.delete()
        messages.success(request, '✅ Direccion eliminada exitosamente')
        return redirect('direcciones')
    
    return render(request, 'custom_admin/direccion.html', {
        'object': direcciones,
        'type': 'direccion'
    })

# Gestión de stock
@login_required(login_url='login')
def stock(request):
    if not request.user.is_staff:
        return redirect('home')

    sort_options = {
        'nombre_asc': (
            'producto__nombre', 'color__nombre', 'talle__order',
            'talle__abbreviation',
        ),
        'nombre_desc': (
            '-producto__nombre', 'color__nombre', 'talle__order',
            'talle__abbreviation',
        ),
        'color_asc': (
            'color__nombre', 'producto__nombre', 'talle__order',
            'talle__abbreviation',
        ),
        'talle_asc': (
            'talle__order', 'talle__abbreviation', 'producto__nombre',
            'color__nombre',
        ),
        'stock_desc': (
            '-stock', 'producto__nombre', 'color__nombre',
            'talle__order', 'talle__abbreviation',
        ),
        'stock_asc': (
            'stock', 'producto__nombre', 'color__nombre',
            'talle__order', 'talle__abbreviation',
        ),
    }
    sort_by = request.GET.get('orden', 'nombre_asc')
    if sort_by not in sort_options:
        sort_by = 'nombre_asc'
    search_query = request.GET.get('buscar', '').strip()

    stock_items = ProductoStock.objects.select_related(
        'producto', 'color', 'talle',
    )
    if search_query:
        stock_items = stock_items.filter(
            Q(producto__nombre__icontains=search_query)
            | Q(producto__codigo__icontains=search_query)
            | Q(color__nombre__icontains=search_query)
            | Q(talle__nombre__icontains=search_query)
            | Q(talle__abbreviation__icontains=search_query)
        )
    stock_items = stock_items.order_by(*sort_options[sort_by])

    grouped_items = {}
    for item in stock_items:
        normalized_name = unicodedata.normalize(
            'NFKD', item.producto.nombre,
        )
        first_character = ''.join(
            character
            for character in normalized_name
            if not unicodedata.combining(character)
        )[:1].upper()
        letter = first_character if first_character in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' else '#'
        grouped_items.setdefault(letter, []).append(item)

    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    letter_groups = [
        {'letter': letter, 'items': grouped_items[letter]}
        for letter in letters
        if letter in grouped_items
    ]
    if '#' in grouped_items:
        letter_groups.append({'letter': '#', 'items': grouped_items['#']})

    return render(
        request,
        'custom_admin/stock.html',
        {
            'letter_groups': letter_groups,
            'alphabet': letters,
            'available_letters': set(grouped_items),
            'search_query': search_query,
            'sort_by': sort_by,
            'total_stock_items': sum(len(group['items']) for group in letter_groups),
        },
    )


@login_required(login_url='login')
def recibir_stock(request):
    if not request.user.is_staff:
        return redirect('home')

    # Consulta JSON asíncrona para buscar producto por código de barras
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'buscar_codigo' in request.GET:
        codigo = request.GET.get('buscar_codigo', '').strip()
        producto = Producto.objects.filter(codigo=codigo).first()
        if not producto:
            return JsonResponse({'success': False, 'error': f'No se encontró un artículo con el código {codigo}.'})
        
        # Obtener los stocks actuales de las variantes de este producto
        stocks = list(ProductoStock.objects.filter(producto=producto).values('color_id', 'talle_id', 'stock'))
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo': producto.codigo,
                'precio': float(producto.precio),
                'estilo_id': producto.estilo_id,
                'tipo_id': producto.tipo_id,
            },
            'stocks': stocks,
        })

    if request.method == 'POST':
        form = IngresoStockPorLectorForm(request.POST)
        if form.is_valid():
            color = form.cleaned_data['color']
            talle = form.cleaned_data['talle']
            estilo = form.cleaned_data.get('estilo')
            tipo = form.cleaned_data.get('tipo')
            cantidad = form.cleaned_data.get('cantidad') or 1
            request.session['recepcion_stock_color'] = color.pk
            request.session['recepcion_stock_talle'] = talle.pk
            codigo = form.cleaned_data['codigo']
            database = router.db_for_write(ProductoStock)
            producto = Producto.objects.using(database).filter(
                codigo=codigo,
            ).first()

            if producto is None:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'No se encontró un artículo con el código {codigo}. No se modificó el stock.'
                    })
                messages.error(
                    request,
                    f'No se encontró un artículo con el código {codigo}. '
                    'No se modificó el stock.',
                )
            else:
                # Si se enviaron estilo o tipo, actualizar el producto
                campos_a_actualizar = []
                if estilo is not None and producto.estilo != estilo:
                    producto.estilo = estilo
                    campos_a_actualizar.append('estilo')
                if tipo is not None and producto.tipo != tipo:
                    producto.tipo = tipo
                    campos_a_actualizar.append('tipo')
                if campos_a_actualizar:
                    producto.save(update_fields=campos_a_actualizar)

                with transaction.atomic(using=database):
                    stock, creado = ProductoStock.objects.using(
                        database,
                    ).get_or_create(
                        producto=producto,
                        color=color,
                        talle=talle,
                        defaults={'stock': cantidad},
                    )
                    if not creado:
                        ProductoStock.objects.using(database).filter(
                            pk=stock.pk,
                        ).update(stock=F('stock') + cantidad)
                        stock.refresh_from_db(using=database)
                    producto.sync_active_status_with_stock()

                msg = (
                    f'{producto.nombre}: stock de {color.nombre}, talle '
                    f'{talle.abbreviation} actualizado a {stock.stock} (+{cantidad}).'
                )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    stocks = list(ProductoStock.objects.filter(producto=producto).values('color_id', 'talle_id', 'stock'))
                    return JsonResponse({
                        'success': True,
                        'mensaje': msg,
                        'nuevo_stock': stock.stock,
                        'producto_id': producto.id,
                        'producto_nombre': producto.nombre,
                        'color_id': color.id,
                        'talle_id': talle.id,
                        'estilo_id': producto.estilo_id,
                        'tipo_id': producto.tipo_id,
                        'stocks': stocks,
                    })

                messages.success(request, msg)

            return redirect('recibir_stock')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Formulario inválido. Verificá que los datos ingresados sean correctos.'
                })
    else:
        form = IngresoStockPorLectorForm(initial={
            'color': request.session.get('recepcion_stock_color'),
            'talle': request.session.get('recepcion_stock_talle'),
            'cantidad': 1,
        })

    return render(
        request,
        'custom_admin/stock_recepcion.html',
        {'form': form},
    )


@login_required(login_url='login')
def editar_stock(request, pk):
    if not request.user.is_staff:
        return redirect('home')

    item = get_object_or_404(
        ProductoStock.objects.select_related('producto', 'color', 'talle'),
        pk=pk,
    )
    quantity_form = StockQuantityForm(initial={'stock': item.stock})
    barcode_form = StockBarcodeForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'guardar':
            quantity_form = StockQuantityForm(request.POST)
            if quantity_form.is_valid():
                item.stock = quantity_form.cleaned_data['stock']
                item.save(update_fields=['stock'])
                messages.success(
                    request,
                    f'Stock de {item.producto.nombre} actualizado a {item.stock} unidades.',
                )
                return redirect('editar_stock', pk=item.pk)
        elif action == 'escanear':
            barcode_form = StockBarcodeForm(request.POST)
            if barcode_form.is_valid():
                codigo = barcode_form.cleaned_data['codigo']
                if not item.producto.codigo or codigo != item.producto.codigo:
                    messages.error(
                        request,
                        'El código leído no corresponde a este artículo. No se modificó el stock.',
                    )
                else:
                    with transaction.atomic():
                        ProductoStock.objects.filter(pk=item.pk).update(
                            stock=F('stock') + 1,
                        )
                    item.refresh_from_db()
                    item.producto.sync_active_status_with_stock()
                    quantity_form = StockQuantityForm(initial={'stock': item.stock})
                    messages.success(
                        request,
                        f'{item.producto.nombre}: stock actualizado a {item.stock} unidades.',
                    )
                return redirect('editar_stock', pk=item.pk)
        else:
            messages.error(request, 'No se reconoció la acción solicitada.')

    return render(
        request,
        'custom_admin/stock_editar.html',
        {
            'item': item,
            'quantity_form': quantity_form,
            'barcode_form': barcode_form,
        },
    )


def health_check(request):
    from django.http import HttpResponse
    return HttpResponse("OK", content_type="text/plain")


@login_required(login_url='login')
def api_agregar_color(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    nombre = request.POST.get('nombre', '').strip()
    hex_code = request.POST.get('hex_code', '').strip() or '#000000'
    order = request.POST.get('order', 0)

    if not nombre:
        return JsonResponse({'success': False, 'error': 'El nombre del color es obligatorio.'})

    if Color.objects.filter(nombre__iexact=nombre).exists():
        color_existente = Color.objects.filter(nombre__iexact=nombre).first()
        return JsonResponse({
            'success': True,
            'id': color_existente.id,
            'nombre': color_existente.nombre,
            'mensaje': 'El color ya existía y fue seleccionado.',
        })

    try:
        order = int(order) if order else 0
    except (ValueError, TypeError):
        order = 0

    nuevo_color = Color.objects.create(
        nombre=nombre,
        hex_code=hex_code,
        order=order,
        esta_activo=True,
    )
    return JsonResponse({
        'success': True,
        'id': nuevo_color.id,
        'nombre': nuevo_color.nombre,
    })


@login_required(login_url='login')
def api_agregar_talle(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    abbreviation = request.POST.get('abbreviation', '').strip().upper()
    nombre = request.POST.get('nombre', '').strip() or abbreviation
    order = request.POST.get('order', 0)

    if not abbreviation:
        return JsonResponse({'success': False, 'error': 'La abreviatura del talle es obligatoria (ej: M, L, 42).'})

    if Talle.objects.filter(abbreviation__iexact=abbreviation).exists():
        talle_existente = Talle.objects.filter(abbreviation__iexact=abbreviation).first()
        return JsonResponse({
            'success': True,
            'id': talle_existente.id,
            'nombre': talle_existente.abbreviation,
            'mensaje': 'El talle ya existía y fue seleccionado.',
        })

    try:
        order = int(order) if order else 0
    except (ValueError, TypeError):
        order = 0

    nuevo_talle = Talle.objects.create(
        abbreviation=abbreviation,
        nombre=nombre,
        order=order,
        esta_activo=True,
    )
    return JsonResponse({
        'success': True,
        'id': nuevo_talle.id,
        'nombre': nuevo_talle.abbreviation,
    })


@login_required(login_url='login')
def api_crear_producto_rapido(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    codigo = request.POST.get('codigo', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    precio = request.POST.get('precio', '0').strip()
    descripcion = request.POST.get('descripcion', '').strip() or f'Artículo {nombre}'

    if not codigo:
        return JsonResponse({'success': False, 'error': 'El código de barras es obligatorio.'})
    if not nombre:
        return JsonResponse({'success': False, 'error': 'El nombre del artículo es obligatorio.'})

    estilo_id = request.POST.get('estilo')
    tipo_id = request.POST.get('tipo')

    try:
        precio_val = float(precio) if precio else 0.0
    except ValueError:
        precio_val = 0.0

    if Producto.objects.filter(codigo=codigo).exists():
        producto = Producto.objects.filter(codigo=codigo).first()
    else:
        producto = Producto.objects.create(
            codigo=codigo,
            nombre=nombre,
            precio=precio_val,
            descripcion=descripcion,
            estilo_id=estilo_id if estilo_id else None,
            tipo_id=tipo_id if tipo_id else None,
            esta_activo=True,
        )

    stocks = list(ProductoStock.objects.filter(producto=producto).values('color_id', 'talle_id', 'stock'))
    return JsonResponse({
        'success': True,
        'producto': {
            'id': producto.id,
            'nombre': producto.nombre,
            'codigo': producto.codigo,
            'precio': float(producto.precio),
            'estilo_id': producto.estilo_id,
            'tipo_id': producto.tipo_id,
        },
        'stocks': stocks,
    })


@login_required(login_url='login')
def api_agregar_estilo(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    nombre = request.POST.get('nombre', '').strip()
    order = request.POST.get('order', 0)

    if not nombre:
        return JsonResponse({'success': False, 'error': 'El nombre del estilo es obligatorio.'})

    if Estilo.objects.filter(nombre__iexact=nombre).exists():
        estilo_existente = Estilo.objects.filter(nombre__iexact=nombre).first()
        return JsonResponse({
            'success': True,
            'id': estilo_existente.id,
            'nombre': estilo_existente.nombre,
            'mensaje': 'El estilo ya existía y fue seleccionado.',
        })

    try:
        order = int(order) if order else 0
    except (ValueError, TypeError):
        order = 0

    nuevo_estilo = Estilo.objects.create(
        nombre=nombre,
        order=order,
        esta_activo=True,
    )
    return JsonResponse({
        'success': True,
        'id': nuevo_estilo.id,
        'nombre': nuevo_estilo.nombre,
    })


@login_required(login_url='login')
def api_agregar_tipo(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    nombre = request.POST.get('nombre', '').strip()
    order = request.POST.get('order', 0)

    if not nombre:
        return JsonResponse({'success': False, 'error': 'El tipo de tela es obligatorio.'})

    if Tipo.objects.filter(nombre__iexact=nombre).exists():
        tipo_existente = Tipo.objects.filter(nombre__iexact=nombre).first()
        return JsonResponse({
            'success': True,
            'id': tipo_existente.id,
            'nombre': tipo_existente.nombre,
            'mensaje': 'El tipo de tela ya existía y fue seleccionado.',
        })

    try:
        order = int(order) if order else 0
    except (ValueError, TypeError):
        order = 0

    nuevo_tipo = Tipo.objects.create(
        nombre=nombre,
        order=order,
        esta_activo=True,
    )
    return JsonResponse({
        'success': True,
        'id': nuevo_tipo.id,
        'nombre': nuevo_tipo.nombre,
    })


@login_required(login_url='login')
def api_deshacer_stock(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    producto_id = request.POST.get('producto_id')
    color_id = request.POST.get('color_id')
    talle_id = request.POST.get('talle_id')
    cantidad = request.POST.get('cantidad', 1)

    try:
        cantidad = int(cantidad)
    except (ValueError, TypeError):
        cantidad = 1

    stock_item = ProductoStock.objects.filter(
        producto_id=producto_id,
        color_id=color_id,
        talle_id=talle_id,
    ).first()

    if not stock_item:
        return JsonResponse({'success': False, 'error': 'Variante de stock no encontrada.'})

    with transaction.atomic():
        nuevo_stock = max(0, stock_item.stock - cantidad)
        stock_item.stock = nuevo_stock
        stock_item.save(update_fields=['stock'])
        stock_item.producto.sync_active_status_with_stock()

    stocks = list(ProductoStock.objects.filter(producto_id=producto_id).values('color_id', 'talle_id', 'stock'))
    return JsonResponse({
        'success': True,
        'mensaje': f'Se restaron {cantidad} u. Nuevo stock: {nuevo_stock}.',
        'nuevo_stock': nuevo_stock,
        'stocks': stocks,
    })


def importar_datos_maestros(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No autorizado")
    
    try:
        from migrate_prestashop import migrate_data
        from vincular_fotos import vincular_imagenes
        migrate_data()
        vincular_imagenes()
        from django.http import HttpResponse
        return HttpResponse("✅ Datos e imágenes vinculados correctamente. Ya podés volver al home.")
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"❌ Error al importar: {str(e)}")