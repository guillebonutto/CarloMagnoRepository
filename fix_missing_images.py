import os
import django
import sys
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from django.core.files.base import ContentFile
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto

def fix_missing():
    ids = [152, 121, 120, 107, 106]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    for p_id in ids:
        try:
            producto = Producto.objects.get(id=p_id)
            url = f"https://carlomagno.ar/{p_id}-product.html"
            print(f"Buscando [{p_id}] {producto.nombre}...")
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                img_tag = soup.find('img', {'itemprop': 'image'})
                if not img_tag:
                    img_tag = soup.find('img', {'class': 'js-qv-product-cover'})
                
                if img_tag and img_tag.get('src'):
                    img_url = img_tag.get('src')
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    print(f"URL: {img_url}")
                    
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    if img_response.status_code == 200:
                        file_name = f"fix_{p_id}.jpg"
                        producto.imagen.save(file_name, ContentFile(img_response.content), save=True)
                        print(f"¡Guardado!")
                    else:
                        print(f"Error descarga: {img_response.status_code}")
                else:
                    print(f"No se encontró img tag")
            else:
                print(f"Página no encontrada")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_missing()
