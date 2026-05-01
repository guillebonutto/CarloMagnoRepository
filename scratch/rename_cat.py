import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria

def rename_category():
    try:
        cat = Categoria.objects.get(nombre='Ambo/Pantalon')
        cat.nombre = 'Ambos'
        cat.save()
        print("Categoría 'Ambo/Pantalon' renombrada a 'Ambos'.")
    except Categoria.DoesNotExist:
        if Categoria.objects.filter(nombre='Ambos').exists():
            print("La categoría 'Ambos' ya existe.")
        else:
            Categoria.objects.create(nombre='Ambos')
            print("Categoría 'Ambos' creada.")

if __name__ == '__main__':
    rename_category()
