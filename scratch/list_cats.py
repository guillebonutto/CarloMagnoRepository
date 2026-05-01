import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria

def list_categories():
    cats = Categoria.objects.all()
    print(f"Existen {cats.count()} categorías:")
    for c in cats:
        print(f"- {c.nombre} (ID: {c.id})")

if __name__ == '__main__':
    list_categories()
