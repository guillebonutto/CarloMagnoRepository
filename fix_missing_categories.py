import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto, Categoria

def fix():
    # Buscar productos en categorías "basura"
    garbage_cats = ['Inicio', 'cat1']
    productos = Producto.objects.filter(categoria__nombre__in=garbage_cats)
    
    print(f"Encontrados {productos.count()} productos en categorías Inicio/cat1.")
    
    for p in productos:
        nombre = p.nombre.lower()
        new_cat = None
        
        if 'campera' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='campera').first()
        elif 'chomba' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='chomba').first()
        elif 'remera' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='remera').first()
        elif 'camisa' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='camisa').first()
        elif 'poleron' in nombre or 'polerón' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='polera').first()
        elif 'pantalón' in nombre or 'pantalón' in nombre:
            new_cat = Categoria.objects.filter(nombre__icontains='pantalón').first()
            
        if new_cat:
            p.categoria = new_cat
            p.save()
            print(f"Reasignado: {p.nombre} -> {new_cat.nombre}")
        else:
            print(f"No se pudo clasificar: {p.nombre}")

if __name__ == "__main__":
    fix()
