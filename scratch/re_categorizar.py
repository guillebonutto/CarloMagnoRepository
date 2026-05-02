import os
import sys
import django

# Configurar Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto, Categoria

def fix_categories():
    print("Iniciando re-categorizacion inteligente...")
    
    # Mapeo de Categoría -> Palabras clave
    # El orden importa: las más específicas primero
    MAPPING = {
        'Ambos': ['ambo'],
        'Camisas': ['camisa'],
        'Remeras': ['remera'],
        'Chombas': ['chomba'],
        'Pantalones': ['pantalon', 'pantalón', 'jean', 'jogger', 'bermuda', 'gabardina', '7/8', 'lino', 'chino'],
        'Sacos/Blazers': ['saco', 'blazer'],
        'Camperas': ['campera', 'impermeable', 'piloto', 'pilotin'],
        'Sweaters & Chalecos': ['sweater', 'sueter', 'suéter', 'chaleco', 'polera', 'polera', 'poleron', 'polerón', 'pullover'],
        'Ropa Interior': ['boxer', 'bóxer', 'interior', 'calzoncillo'],
        'Cintos': ['cinto', 'cinturon', 'cinturón'],
        'Corbatas': ['corbata'],
        'Medias': ['media'],
        'Accesorios': ['pulsera', 'moño', 'accesorio', 'pisa corbata', 'pasador'],
        'Gemelos/Mancuernillas': ['gemelo', 'mancuernilla'],
        'Kits de Regalo': ['kit', 'regalo'],
        'Gift Cards': ['gift card', 'tarjeta regalo'],
    }

    productos = Producto.objects.all()
    count_updated = 0
    
    for p in productos:
        nombre_lower = p.nombre.lower()
        nueva_cat_nombre = None
        
        # Buscar coincidencia en el mapeo
        for cat_nombre, keywords in MAPPING.items():
            if any(key in nombre_lower for key in keywords):
                nueva_cat_nombre = cat_nombre
                break # Encontró la primera coincidencia y sale
        
        if nueva_cat_nombre:
            try:
                # Intentamos obtener la categoría (ignorando mayúsculas/minúsculas si es posible)
                categoria_obj = Categoria.objects.filter(nombre__icontains=nueva_cat_nombre).first()
                
                if not categoria_obj:
                    # Si no existe, la creamos
                    categoria_obj = Categoria.objects.create(nombre=nueva_cat_nombre)
                    print(f"Categoria creada: {nueva_cat_nombre}")
                
                if p.categoria != categoria_obj:
                    old_cat = p.categoria.nombre if p.categoria else "Ninguna"
                    p.categoria = categoria_obj
                    p.save()
                    print(f"OK [{p.nombre}] movido de '{old_cat}' a '{categoria_obj.nombre}'")
                    count_updated += 1
            except Exception as e:
                print(f"ERR con producto {p.nombre}: {e}")

    print(f"\nProceso finalizado. Se actualizaron {count_updated} productos.")

if __name__ == '__main__':
    fix_categories()
