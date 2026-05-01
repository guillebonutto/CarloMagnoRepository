import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria, Producto

def auto_categorize():
    print("Iniciando categorización automática...")
    
    # Mapeo de palabras clave a nombres de categorías creadas
    mapping = {
        'Ambos': ['ambo'],
        'Pantalón': ['pantalón', 'jean', 'bermuda', 'short', 'jogger', 'gabardina'],
        'Camisa': ['camisa'],
        'Remera': ['remera', 't-shirt'],
        'Chomba': ['chomba'],
        'Accesorios': ['cinto', 'corbata', 'billetera', 'media', 'bufanda', 'gorro', 'pañuelo'],
        'Chaleco': ['chaleco'],
        'Saco': ['saco', 'blazer', 'piloto']
    }
    
    # Obtener las categorías de la DB
    cats = {c.nombre: c for c in Categoria.objects.all()}
    
    count = 0
    # Procesamos todos los productos para asegurar que los "ambos" se muevan si están en la categoría errónea
    for p in Producto.objects.all():
        nombre_lower = p.nombre.lower()
        
        # Prioridad especial para Ambos
        if 'ambo' in nombre_lower:
            if 'Ambos' in cats:
                if p.categoria != cats['Ambos']:
                    p.categoria = cats['Ambos']
                    p.save()
                    print(f"Reasignado (Prioridad): '{p.nombre}' -> Ambos")
                    count += 1
                continue

        # Resto de categorías (solo si no tienen categoría)
        if p.categoria is None:
            for cat_nombre, keywords in mapping.items():
                if any(k in nombre_lower for k in keywords):
                    if cat_nombre in cats:
                        p.categoria = cats[cat_nombre]
                        p.save()
                        print(f"Asignado: '{p.nombre}' -> {cat_nombre}")
                        count += 1
                        break
                    
    print(f"Proceso finalizado. Se categorizaron/actualizaron {count} productos.")

if __name__ == '__main__':
    auto_categorize()
