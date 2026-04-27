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
    # PrestaShop image URL logic: img/p/1/2/3/123.jpg
    image_id_str = str(image_id)
    path = "/".join(list(image_id_str))
    return f"https://carlomagno.ar/img/p/{path}/{image_id_str}.jpg"

def migrate_images():
    image_mapping = {
        "24": "36", "37": "145", "38": "146", "39": "147", "41": "148", 
        "42": "151", "47": "153", "49": "154", "53": "158", "54": "159", 
        "55": "160", "56": "161", "57": "162", "58": "163", "59": "164", 
        "60": "165", "64": "172", "65": "173", "67": "175", "68": "176", 
        "69": "177", "70": "178", "71": "179", "74": "184", "75": "185", 
        "78": "191", "79": "193", "81": "196", "82": "197", "83": "198", 
        "89": "204", "91": "206", "92": "207", "93": "208", "95": "210", 
        "98": "213", "100": "215", "102": "217", "103": "218", "104": "219", 
        "106": "221", "107": "222", "108": "223", "110": "225", "113": "228", 
        "115": "230", "116": "231", "117": "232", "118": "233", "119": "234", 
        "120": "235", "121": "236", "125": "240", "127": "242", "128": "243", 
        "134": "249", "141": "256", "143": "258", "146": "261", "147": "262", 
        "148": "263", "150": "265", "151": "266", "152": "267", "153": "268", 
        "155": "270"
    }

    for p_id, img_id in image_mapping.items():
        try:
            producto = Producto.objects.get(id=int(p_id))
            url = get_prestashop_image_url(img_id)
            print(f"Descargando imagen para {producto.nombre}: {url}")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                file_name = f"product_{p_id}.jpg"
                producto.imagen.save(file_name, ContentFile(response.content), save=True)
                print(f"Imagen guardada para {producto.nombre}")
            else:
                print(f"Error {response.status_code} al descargar {url}")
                
        except Producto.DoesNotExist:
            print(f"Producto {p_id} no encontrado")
        except Exception as e:
            print(f"Error con producto {p_id}: {e}")

if __name__ == "__main__":
    migrate_images()
