import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria, Producto

def setup_categories():
    print("Iniciando limpieza de categorías...")
    
    # Desvincular productos de categorías actuales para evitar PROTECT (aunque ya lo cambiamos a SET_NULL)
    Producto.objects.all().update(categoria=None)
    
    # Eliminar categorías existentes
    count = Categoria.objects.count()
    Categoria.objects.all().delete()
    print(f"Se eliminaron {count} categorías.")
    
    # Nuevas categorías
    nuevas = ['Pantalón', 'Camisa', 'Remera', 'Chomba', 'Accesorios', 'Chaleco', 'Saco']
    
    for nombre in nuevas:
        cat = Categoria.objects.create(nombre=nombre)
        print(f"Creada categoría: {nombre}")
        
    print("Proceso finalizado con éxito.")

if __name__ == '__main__':
    setup_categories()
