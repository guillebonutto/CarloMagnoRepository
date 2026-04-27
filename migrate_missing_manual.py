import os
import django
import sys
import requests
from io import BytesIO
from django.core.files.base import ContentFile

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto

def get_prestashop_image_url(image_id):
    image_id_str = str(image_id)
    path = "/".join(list(image_id_str))
    return f"https://carlomagno.ar/img/p/{path}/{image_id_str}.jpg"

def migrate_missing():
    # Mapeo manual obtenido vía SQL
    mapping = {
        "106": "363",
        "107": "365",
        "120": "404",
        "121": "407",
        "152": "469"
    }

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

    for p_id, img_id in mapping.items():
        try:
            producto = Producto.objects.get(id=int(p_id))
            url = get_prestashop_image_url(img_id)
            print(f"Descargando [{p_id}] {producto.nombre}: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                file_name = f"manual_{p_id}.jpg"
                producto.imagen.save(file_name, ContentFile(response.content), save=True)
                print(f"¡Éxito!")
            else:
                print(f"Error {response.status_code}")
                
        except Producto.DoesNotExist:
            print(f"Producto {p_id} no encontrado")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    migrate_missing()
