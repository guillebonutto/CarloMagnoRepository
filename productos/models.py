from django.db import models
from django.core.validators import MinValueValidator
from PIL import Image
from django_countries.fields import CountryField
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
import sys

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Color(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    hex_code = models.CharField(
        max_length=7, 
        verbose_name='Código Hexadecimal',
        help_text='Formato: #RRGGBB (ejemplo: #FF0000 para rojo)',
        default='#000000'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colores'
        ordering = ['order', 'nombre']

    def __str__(self):
        return self.nombre


class Talle(models.Model):
    nombre = models.CharField(max_length=20, unique=True, verbose_name='Talle')
    abbreviation = models.CharField(
        max_length=10, 
        verbose_name='Abreviatura',
        help_text='Ej: XS, S, M, L, XL'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Talle'
        verbose_name_plural = 'Talles'
        ordering = ['order', 'nombre']

    def __str__(self):
        return f"{self.abbreviation} - {self.nombre}"


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    logo = models.ImageField(
        upload_to='marcas/',
        null=True,
        blank=True,
        verbose_name='Logo'
    )
    website = models.URLField(blank=True, verbose_name='Sitio web')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(verbose_name='Descripción')
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name='Precio'
    )
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT, 
        related_name='categorias',
        verbose_name='Categoría'
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Marca'
    )
    talle = models.ForeignKey(
        Talle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        verbose_name='Talle'
    )
    colores = models.ManyToManyField(
        Color,
        related_name='productos',
        verbose_name='Colores disponibles',
        blank=True
    )
    imagen = models.ImageField(
        upload_to='productos/', 
        null=True, 
        blank=True,
        verbose_name='Imagen principal'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        """Redimensionar imagen automáticamente antes de guardar"""
        if self.imagen:
            self.imagen = self.resize_image(self.imagen)
        super().save(*args, **kwargs)
    
    def resize_image(self, image_field):
        """Redimensiona la imagen a 450x563px manteniendo proporción con fondo blanco"""
        try:
            # Abrir la imagen
            img = Image.open(image_field)
            
            # Convertir a RGB si es necesario (para PNG con transparencia)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Crear fondo blanco
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calcular las nuevas dimensiones manteniendo proporción
            img.thumbnail((450, 563), Image.Resampling.LANCZOS)
            
            # Crear canvas de 450x563 con fondo blanco
            canvas = Image.new('RGB', (450, 563), (255, 255, 255))
            
            # Centrar la imagen en el canvas
            offset_x = (450 - img.width) // 2
            offset_y = (563 - img.height) // 2
            canvas.paste(img, (offset_x, offset_y))
            
            # Guardar en memoria
            output = BytesIO()
            canvas.save(output, format='PNG', quality=95, optimize=True)
            output.seek(0)
            
            # Crear nuevo archivo
            original_name = image_field.name.split('/')[-1]
            base_name = original_name.rsplit('.', 1)[0]
            new_name = f"{base_name}_450x563.png"
            
            return InMemoryUploadedFile(
                output,
                'ImageField',
                new_name,
                'image/png',
                sys.getsizeof(output),
                None
            )
        except Exception as e:
            print(f"Error al redimensionar imagen: {e}")
            return image_field
    
    def get_colores_disponibles(self):
        """Retorna los colores disponibles para este producto"""
        return self.colores.all()
    
    def get_talles_disponibles(self):
        """Retorna los talles disponibles para este producto"""
        return Talle.objects.filter(
            productostock__producto=self
        ).distinct()


class ProductoStock(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='stock_items',
        verbose_name='Producto'
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        related_name='productostock',
        verbose_name='Color'
    )
    talle = models.ForeignKey(
        Talle,
        on_delete=models.PROTECT,
        related_name='productostock',
        verbose_name='Talle'
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock disponible'
    )

    class Meta:
        verbose_name = 'Stock de producto'
        verbose_name_plural = 'Stock de productos'
        unique_together = ['producto', 'color', 'talle']
        ordering = ['producto', 'color__order', 'talle__order']

    def __str__(self):
        return f"{self.producto.nombre} - {self.color.nombre} - {self.talle.abbreviation}: {self.stock} unidades"


class GrupoCliente(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Grupo')
    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Descuento (%)',
        help_text='Porcentaje de descuento para este grupo'
    )

    class Meta:
        verbose_name = 'Grupo de Cliente'
        verbose_name_plural = 'Grupos de Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    TRATAMIENTO_CHOICES = [
        ('SR', 'Sr.'),
        ('SRA', 'Sra.'),
        ('SRTA', 'Srta.'),
        ('DR', 'Dr.'),
        ('DRA', 'Dra.'),
    ]

    tratamiento = models.CharField(
        max_length=10,
        choices=TRATAMIENTO_CHOICES,
        default='SR',
        verbose_name='Tratamiento'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    grupo = models.ForeignKey(
        GrupoCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Grupo'
    )
    ventas_totales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Ventas Totales'
    )
    activado = models.BooleanField(default=True, verbose_name='Cuenta Activada')
    boletin = models.BooleanField(default=False, verbose_name='Suscrito a Boletín')
    ofertas_asociados = models.BooleanField(default=False, verbose_name='Ofertas de Asociados')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    ultima_visita = models.DateTimeField(null=True, blank=True, verbose_name='Última Visita')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.get_tratamiento_display()} {self.nombre} {self.apellidos}"


class Direccion(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='direcciones',
        verbose_name='Cliente'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    direccion = models.CharField(max_length=200, verbose_name='Dirección')
    codigo_postal = models.CharField(max_length=20, verbose_name='Código Postal/Zip')
    ciudad = models.CharField(max_length=100, verbose_name='Ciudad')
    pais = CountryField(blank_label='(Seleccionar país)', verbose_name='País')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    es_predeterminada = models.BooleanField(default=False, verbose_name='Dirección Predeterminada')

    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        ordering = ['-es_predeterminada', 'cliente']

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.ciudad}, {self.pais}"
    
class Carrito(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Usuario'
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name='ID de Sesión'
    )
    creado = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    actualizado = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')

    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
        ordering = ['-actualizado']

    def __str__(self):
        return f"Carrito {self.id} - {self.usuario or self.session_key}"

    def get_total(self):
        """Calcula el total del carrito"""
        return sum(item.get_subtotal() for item in self.items.all())

    def get_cantidad_total(self):
        """Obtiene la cantidad total de productos"""
        return sum(item.cantidad for item in self.items.all())


class CarritoItem(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Carrito'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        verbose_name='Color'
    )
    talle = models.ForeignKey(
        Talle,
        on_delete=models.CASCADE,
        verbose_name='Talle'
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    agregado = models.DateTimeField(auto_now_add=True, verbose_name='Agregado')

    class Meta:
        verbose_name = 'Item del Carrito'
        verbose_name_plural = 'Items del Carrito'
        unique_together = ['carrito', 'producto', 'color', 'talle']

    def __str__(self):
        return f"{self.producto.nombre} - {self.color.nombre} - {self.talle.abbreviation} x{self.cantidad}"

    def get_subtotal(self):
        """Calcula el subtotal del item"""
        return self.producto.precio * self.cantidad

    def get_stock_disponible(self):
        """Obtiene el stock disponible para esta combinación"""
        try:
            stock = ProductoStock.objects.get(
                producto=self.producto,
                color=self.color,
                talle=self.talle
            )
            return stock.stock
        except ProductoStock.DoesNotExist:
            return 0