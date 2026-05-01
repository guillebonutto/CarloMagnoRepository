import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria, Producto

def list_ambos():
    ambos = Producto.objects.filter(nombre__icontains='ambo')
    print(f"Encontrados {ambos.count()} productos con 'ambo' en el nombre:")
    for p in ambos:
        print(f"- {p.nombre} (Categoría actual: {p.categoria})")

if __name__ == '__main__':
    list_ambos()
