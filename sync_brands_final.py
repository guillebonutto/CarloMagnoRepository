import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto, Marca

mapping = {
    'Yves Saint Laurent': [
        'Camisas Vestir Regular', 'Camisas Sport con Bolsillo', 'Chomba Fantasia.', 
        'Boxer', 'Camisa Lisa Slim', 'Camisa Lisa Vestir', 'Chomba Pique.', 
        'Chomba pique', 'Chombas de Jersey', 'Chombas lisa Pique.', 'Remera Lisa', 
        'Camisa Manga Corta', 'Camisas Manga corta.', 'Campera micro polar', 
        'Chomba manga larga', 'Campera algodón .', 'Camisa Sport', 'camisa sport', 
        'campera impermeable'
    ],
    'Rochas Paris': [
        'Rochas Paris', 'Jeans Rochas', 'Ambo', 'Pantalón Lino.', 'Saco sport pura lana', 
        'Campera', 'campera lana', 'Chaleco', 'campera', 'Piloto'
    ],
    'Pierre Cardin': [
        'Jean clásico cinco bolsillos', 'Accesorios', 'Pantalón Gabardina', 'Cintos.', 
        'Bermuda Algodon', 'Medias', 'Poleron', 'Chaleco', 'Suéter medio cierre merino', 
        'Polerón pura lana .', 'campera', 'sweater', 'saco sport', 'sweaters'
    ],
    'Christian Lacroix': [
        'Remera Manga Larga', 'Jogger Gabardina discontinuos', 'Joggers Algodón.', 
        'Remeras manga corta', 'Bermuda Gabardina', 'Chomba Pique lisa'
    ]
}

def sync():
    # Cleanup duplicates
    for m in Marca.objects.all():
        if m.nombre.lower() == 'pierre cardin' and m.nombre != 'Pierre Cardin':
            m.nombre = 'Pierre Cardin'
            m.save()
        if m.nombre.lower() == 'yvessaintlaurent' or m.nombre.lower() == 'yves saint laurent':
            m.nombre = 'Yves Saint Laurent'
            m.save()

    for brand_name, product_names in mapping.items():
        marca, _ = Marca.objects.get_or_create(nombre=brand_name)
        for name in product_names:
            # Match by name EXACT first to avoid collisions
            productos = Producto.objects.filter(nombre__iexact=name.strip())
            
            for p in productos:
                p.marca = marca
                p.save()
                print(f"Sincronizado (Exact): {p.nombre} -> {brand_name}")

if __name__ == "__main__":
    sync()
