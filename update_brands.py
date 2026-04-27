import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto, Marca

mapping = {
    'YvesSaintLaurent': [102, 118, 120, 121, 125, 147, 148],
    'Rochas Paris': [37, 53, 55, 62, 65, 83, 86, 91, 111, 113, 114],
    'Pierre cardin': [24, 39, 42, 59, 81, 92, 108, 110, 115, 119, 143, 146, 150, 159],
    'Christian Lacronix': [54, 60, 70, 78, 82, 89]
}

def update():
    for brand_name, ids in mapping.items():
        marca, _ = Marca.objects.get_or_create(nombre=brand_name)
        for pid in ids:
            try:
                p = Producto.objects.get(id=pid)
                p.marca = marca
                p.save()
                print(f"Actualizado: {p.nombre} -> {brand_name}")
            except Producto.DoesNotExist:
                print(f"Producto {pid} no encontrado localmente.")

if __name__ == "__main__":
    update()
