from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as django_login, authenticate
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.forms import ModelForm
from django import forms
from productos.models import Producto, Categoria, Color, Marca, Talle, Cliente, Direccion, ProductoStock, Pedido, PedidoItem, Cupon
from productos.forms import ProductoForm
from django.db.models import Sum, Count, Avg
from django.db.models.functions import ExtractMonth

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

# Dashboard
@login_required(login_url='login')
def dashboard(request):
    if not request.user.is_staff:
        return redirect('inicio')
    
    # Métricas de Ventas Reales
    ventas_totales = Pedido.objects.filter(estado_pago='pagado').aggregate(Sum('total'))['total__sum'] or 0
    cantidad_pedidos = Pedido.objects.filter(estado_pago='pagado').count()
    ticket_promedio = Pedido.objects.filter(estado_pago='pagado').aggregate(Avg('total'))['total__avg'] or 0
    
    # Ventas por Estación (Cálculo dinámico basado en los pedidos existentes)
    estaciones = {
        'Verano': 0,
        'Otoño': 0,
        'Invierno': 0,
        'Primavera': 0
    }
    
    pedidos_pagados = Pedido.objects.filter(estado_pago='pagado')
    for p in pedidos_pagados:
        estacion = p.get_estacion()
        estaciones[estacion] += float(p.total)

    # Impacto de Promociones
    pedidos_con_cupon = Pedido.objects.filter(estado_pago='pagado', cupon__isnull=False).count()
    
    context = {
        'total_productos': Producto.objects.count(),
        'total_categories': Categoria.objects.count(),
        'total_marcas': Marca.objects.count(),
        'low_stock': ProductoStock.objects.filter(stock__lt=5).count(),
        
        # Nuevas métricas Shein/AliExpress
        'ventas_totales': ventas_totales,
        'cantidad_pedidos': cantidad_pedidos,
        'ticket_promedio': ticket_promedio,
        'estaciones_data': estaciones,
        'pedidos_con_cupon': pedidos_con_cupon,
        'recent_pedidos': Pedido.objects.order_by('-fecha_creacion')[:5],
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
    
    # Queryset base
    productos_qs = Producto.objects.select_related('categoria', 'marca').all()
    
    # Aplicar filtros
    if cat_filter and cat_filter.isdigit():
        try:
            from django.db.models import Q
            # Filtramos por la categoría seleccionada O por cualquier subcategoría que la tenga como padre
            subcategorias_ids = Categoria.objects.filter(parent_id=cat_filter).values_list('id', flat=True)
            productos_qs = productos_qs.filter(Q(categoria_id=cat_filter) | Q(categoria_id__in=subcategorias_ids))
        except Exception:
            pass
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

# Gestión de categorías
@login_required(login_url='login')
def categorias(request):
    if not request.user.is_staff:
        return redirect('home')
    
    categories = Categoria.objects.all()
    return render(request, 'custom_admin/categorias.html', {'categories': categories})

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
    
    stock_items = ProductoStock.objects.select_related('producto', 'color', 'talle').all()
    return render(request, 'custom_admin/stock.html', {'stock_items': stock_items})