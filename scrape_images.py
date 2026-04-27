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

def scrape_and_migrate_images():
    productos = Producto.objects.all()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    for producto in productos:
        try:
            # Intentar acceder por ID
            url = f"https://carlomagno.ar/{producto.id}-product.html"
            print(f"Buscando imagen para [{producto.id}] {producto.nombre} en {url}...")
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar la imagen principal
                # PrestaShop suele usar class="js-qv-product-cover" o itemprop="image"
                img_tag = soup.find('img', {'itemprop': 'image'})
                if not img_tag:
                    img_tag = soup.find('img', {'class': 'js-qv-product-cover'})
                if not img_tag:
                    # Buscar cualquier imagen que parezca del producto
                    img_tag = soup.find('img', {'class': 'img-fluid'})
                
                if img_tag and img_tag.get('src'):
                    img_url = img_tag.get('src')
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = 'https://carlomagno.ar' + img_url
                    
                    print(f"Imagen encontrada: {img_url}")
                    
                    # Descargar imagen
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    if img_response.status_code == 200:
                        file_name = f"product_{producto.id}.jpg"
                        producto.imagen.save(file_name, ContentFile(img_response.content), save=True)
                        print(f"¡Éxito! Imagen guardada para {producto.nombre}")
                    else:
                        print(f"Error {img_response.status_code} al descargar imagen de {img_url}")
                else:
                    print(f"No se encontró etiqueta de imagen en la página para {producto.nombre}")
            else:
                print(f"Error {response.status_code} al acceder a la página del producto {producto.id}")
            
            # Pequeño delay para no saturar
            time.sleep(1)
            
        except Exception as e:
            print(f"Error procesando producto {producto.id}: {e}")

if __name__ == "__main__":
    scrape_and_migrate_images()
