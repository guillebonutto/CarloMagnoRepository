import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Color

def fix_colors():
    color_map = {
        'Amarillo': '#FFFF00',
        'Azul': '#000080',  # Navy
        'Beige': '#F5F5DC',
        'Blanco': '#FFFFFF',
        'Bordo': '#800000',
        'Camel': '#C19A6B',
        'Celeste': '#87CEEB',
        'Gris': '#808080',
        'Gris pardo': '#483C32',
        'Negro': '#000000',
        'Rojo': '#FF0000',
        'Rosa': '#FFC0CB',
        'Verde': '#008000',
        'Verde Militar': '#4B5320',
        'red': '#FF0000',
    }

    for name, hex_code in color_map.items():
        try:
            color = Color.objects.get(nombre=name)
            color.hex_code = hex_code
            color.save()
            print(f"Color {name} actualizado a {hex_code}")
        except Color.DoesNotExist:
            # Si no existe, lo creamos para que esté disponible
            Color.objects.create(nombre=name, hex_code=hex_code)
            print(f"Color {name} creado con {hex_code}")

if __name__ == "__main__":
    fix_colors()
