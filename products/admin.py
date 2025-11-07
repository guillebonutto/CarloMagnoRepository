from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Color, Talle, Marca, Producto, ProductoStock, Cliente, GrupoCliente, Direccion, Carrito, CarritoItem

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'producto_count']
    search_fields = ['nombre']
    
    def producto_count(self, obj):
        count = obj.categorias.count()  # ← Corregido
        return format_html(
            '<span style="background: #e3f2fd; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{} productos</span>',  # ← Corregido
            count
        )
    producto_count.short_description = 'Cantidad de productos'  # ← Corregido


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['color_preview', 'nombre', 'hex_code', 'order', 'producto_count']
    list_editable = ['order']
    search_fields = ['nombre']
    ordering = ['order', 'nombre']
    
    def color_preview(self, obj):
        border = 'border: 1px solid #ccc;' if obj.hex_code in ['#FFFFFF', '#ffffff'] else ''
        return format_html(
            '<div style="width: 40px; height: 40px; background: {}; border-radius: 5px; {}"></div>',
            obj.hex_code, border
        )
    color_preview.short_description = 'Vista previa'
    
    def producto_count(self, obj):
        count = obj.productos.count()
        return f"{count} productos"  # ← Corregido
    producto_count.short_description = 'En productos'  # ← Corregido


@admin.register(Talle)
class TalleAdmin(admin.ModelAdmin):
    list_display = ['abbreviation', 'nombre', 'order', 'producto_count']
    list_editable = ['order']
    search_fields = ['nombre', 'abbreviation']
    ordering = ['order']
    
    def producto_count(self, obj):
        count = obj.productos.count()
        return f"{count} productos"
    producto_count.short_description = 'En productos'  # ← Corregido


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'logo_preview', 'website', 'producto_count']
    search_fields = ['nombre']
    readonly_fields = ['logo_preview']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Sitio web', {
            'fields': ('website',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; border-radius: 10px;" />',
                obj.logo.url
            )
        return "Sin logo"
    logo_preview.short_description = 'Vista previa del logo'
    
    def producto_count(self, obj):
        count = obj.productos.count()
        return format_html(
            '<span style="background: #e8f5e9; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{} productos</span>',  # ← Corregido
            count
        )
    producto_count.short_description = 'Productos'


class ProductoStockInline(admin.TabularInline):  # ← Nombre corregido
    model = ProductoStock
    extra = 3
    fields = ['color', 'talle', 'stock']
    autocomplete_fields = ['color', 'talle']
    

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):  # ← Nombre corregido
    list_display = ['nombre', 'marca', 'categoria', 'precio', 'image_thumbnail', 'colores_display', 'created_at']
    list_filter = ['categoria', 'marca', 'colores', 'created_at']
    search_fields = ['nombre', 'descripcion', 'marca__nombre']
    inlines = [ProductoStockInline]
    readonly_fields = ['image_preview', 'created_at', 'updated_at']
    filter_horizontal = ['colores']
    autocomplete_fields = ['marca', 'categoria']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'marca', 'precio'),
            'description': 'Información principal del producto'  # ← Corregido (debe ser 'description')
        }),
        ('Atributos', {
            'fields': ('colores',),
            'description': 'Colores disponibles para este producto'  # ← Corregido
        }),
        ('Imagen', {
            'fields': ('imagen', 'image_preview'),
            'description': '⚠️ La imagen se redimensionará automáticamente a 450x563px al guardar'  # ← Corregido
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_thumbnail(self, obj):
        """Miniatura para la lista de productos"""
        if obj.imagen:  # ← Corregido (era obj.image)
            return format_html(
                '<img src="{}" style="width: 50px; height: 62.5px; object-fit: cover; border-radius: 5px;" />',
                obj.imagen.url  # ← Corregido
            )
        return "❌"
    image_thumbnail.short_description = '🖼️'

    def image_preview(self, obj):
        """Vista previa grande en el formulario"""
        if obj.imagen:  # ← Corregido (era obj.image)
            return format_html(
                '<div style="margin-top: 10px;">'
                '<img src="{}" style="max-width: 450px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                '<p style="color: #666; margin-top: 10px;">✅ Esta imagen está en formato 450x563px</p>'
                '</div>',
                obj.imagen.url  # ← Corregido
            )
        return '<p style="color: #999;">No hay imagen cargada</p>'
    image_preview.short_description = 'Vista previa actual'
    
    def colores_display(self, obj):
        """Mostrar colores disponibles"""
        colores = obj.colores.all()[:3]
        html = ''
        for color in colores:
            border = 'border: 1px solid #ccc;' if color.hex_code in ['#FFFFFF', '#ffffff'] else ''
            html += f'<span style="display: inline-block; width: 20px; height: 20px; background: {color.hex_code}; border-radius: 50%; margin-right: 3px; {border}"></span>'
        
        total = obj.colores.count()
        if total > 3:
            html += f' <small>+{total - 3}</small>'
        
        return format_html(html) if html else '-'
    colores_display.short_description = 'Colores'


@admin.register(ProductoStock)
class ProductoStockAdmin(admin.ModelAdmin):  # ← Nombre corregido
    list_display = ['producto', 'color_badge', 'talle_badge', 'stock', 'stock_status']
    list_filter = ['color', 'talle', 'producto__categoria', 'producto__marca']
    search_fields = ['producto__nombre']
    list_editable = ['stock']
    ordering = ['producto', 'color__order', 'talle__order']
    autocomplete_fields = ['producto', 'color', 'talle']

    def color_badge(self, obj):
        """Mostrar color con badge"""
        border = 'border: 1px solid #ccc;' if obj.color.hex_code in ['#FFFFFF', '#ffffff'] else ''
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background: {}; border-radius: 3px; vertical-align: middle; {}"></span> {}',
            obj.color.hex_code, border, obj.color.nombre
        )
    color_badge.short_description = 'Color'

    def talle_badge(self, obj):
        """Mostrar talle con badge"""
        return format_html(
            '<span style="background: #e3f2fd; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            obj.talle.abbreviation
        )
    talle_badge.short_description = 'Talle'

    def stock_status(self, obj):
        """Estado del stock con emoji"""
        if obj.stock == 0:
            return '❌ Sin stock'
        elif obj.stock < 5:
            return '⚠️ Bajo'
        else:
            return '✅ Disponible'
    stock_status.short_description = 'Estado'

@admin.register(GrupoCliente)
class GrupoClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descuento']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'apellidos', 'email', 'grupo', 'activado', 'fecha_registro']
    list_filter = ['activado', 'boletin', 'grupo']
    search_fields = ['nombre', 'apellidos', 'email']

@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'ciudad', 'pais', 'es_predeterminada']
    list_filter = ['pais', 'es_predeterminada']

class CarritoItemInline(admin.TabularInline):
    model = CarritoItem
    extra = 0
    readonly_fields = ['agregado', 'get_subtotal_display']
    fields = ['producto', 'color', 'talle', 'cantidad', 'get_subtotal_display', 'agregado']
    
    def get_subtotal_display(self, obj):
        if obj.id:
            return format_html(
                '<strong style="color: #8B0000;">${}</strong>',
                obj.get_subtotal()
            )
        return '-'
    get_subtotal_display.short_description = 'Subtotal'


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario_display', 'items_count', 'total_display', 'actualizado']
    list_filter = ['creado', 'actualizado']
    search_fields = ['usuario__username', 'usuario__email', 'session_key']
    readonly_fields = ['creado', 'actualizado', 'total_display']
    inlines = [CarritoItemInline]
    
    fieldsets = (
        ('Información del Carrito', {
            'fields': ('usuario', 'session_key')
        }),
        ('Resumen', {
            'fields': ('total_display',)
        }),
        ('Fechas', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
    
    def usuario_display(self, obj):
        if obj.usuario:
            return format_html(
                '<strong>{}</strong>',
                obj.usuario.username
            )
        return format_html(
            '<span style="color: #999;">Invitado ({})</span>',
            obj.session_key[:10] + '...' if obj.session_key else 'N/A'
        )
    usuario_display.short_description = 'Usuario'
    
    def items_count(self, obj):
        count = obj.items.count()
        cantidad = obj.get_cantidad_total()
        return format_html(
            '<span style="background: #e3f2fd; padding: 3px 10px; border-radius: 10px;">{} items ({} productos)</span>',
            count, cantidad
        )
    items_count.short_description = 'Productos'
    
    def total_display(self, obj):
        return format_html(
            '<strong style="font-size: 18px; color: #8B0000;">${}</strong>',
            obj.get_total()
        )
    total_display.short_description = 'Total'


@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'carrito', 'producto', 'color_badge', 'talle_badge', 'cantidad', 'subtotal_display', 'stock_disponible']
    list_filter = ['color', 'talle', 'agregado']
    search_fields = ['producto__nombre', 'carrito__usuario__username']
    readonly_fields = ['agregado', 'subtotal_display', 'stock_disponible']
    
    def color_badge(self, obj):
        border = 'border: 1px solid #ccc;' if obj.color.hex_code in ['#FFFFFF', '#ffffff'] else ''
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background: {}; border-radius: 3px; vertical-align: middle; {}"></span> {}',
            obj.color.hex_code, border, obj.color.nombre
        )
    color_badge.short_description = 'Color'
    
    def talle_badge(self, obj):
        return format_html(
            '<span style="background: #e3f2fd; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            obj.talle.abbreviation
        )
    talle_badge.short_description = 'Talle'
    
    def subtotal_display(self, obj):
        return format_html(
            '<strong style="color: #8B0000;">${}</strong>',
            obj.get_subtotal()
        )
    subtotal_display.short_description = 'Subtotal'
    
    def stock_disponible(self, obj):
        stock = obj.get_stock_disponible()
        if stock == 0:
            return format_html('<span style="color: #f44336;">❌ Sin stock</span>')
        elif stock < 5:
            return format_html('<span style="color: #ff9800;">⚠️ {} unidades</span>', stock)
        else:
            return format_html('<span style="color: #4caf50;">✅ {} unidades</span>', stock)
    stock_disponible.short_description = 'Stock'