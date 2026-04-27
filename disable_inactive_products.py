import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto

# Lista de nombres de productos a desactivar (obtenida de PrestaShop SQL)
inactive_names = [
    "Joggers Algodón.",
    "Media Polera Algodón.",
    "Chomba Fantasia.",
    "Cintos.",
    "Pulseras Simple cuero",
    "Pulsera Elastica Simple",
    "Pulsera doble piedras",
    "Poleron",
    "Chaleco",
    "Chomba manga larga",
    "Campera algodón .",
    "sweaters",
    "saco sport",
    "camisa",
    "chaleco",
    "campera"
]

def disable():
    for name in inactive_names:
        # Match by name EXACT (case insensitive)
        productos = Producto.objects.filter(nombre__iexact=name)
        if not productos.exists():
            # Try fuzzy match if exact fails
            productos = Producto.objects.filter(nombre__icontains=name.strip('.'))
            
        for p in productos:
            p.esta_activo = False
            p.save()
            print(f"Desactivado: {p.nombre}")

if __name__ == "__main__":
    disable()
