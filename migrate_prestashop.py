import os
import django
import sys
import json

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Categoria, Color, Talle, Producto, ProductoStock

def migrate_data():
    # Cargar datos JSON
    # (Pego aquí los datos extraídos por brevedad, pero en un script real leería un archivo)
    products_data = [
      {"id_product": "24", "product_name": "Jean clásico cinco bolsillos", "category_name": "Jean Lona", "price": "89900.00", "reference": None, "description_short": "<p>Jean regular.</p>"},
      {"id_product": "37", "product_name": "Saco Sport", "category_name": "Saco Sport", "price": "390000.00", "reference": None, "description_short": "<p>Saco Sport.</p>"},
      {"id_product": "38", "product_name": "Camisas Vestir Regular", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": "<p>Camisa vestir algodón y polyester.</p>"},
      {"id_product": "39", "product_name": "Accesorios", "category_name": "Corbatas", "price": "24900.00", "reference": None, "description_short": "<p>Corbatas, Moños</p>"},
      {"id_product": "41", "product_name": "Campera Sport", "category_name": "Campera Algodón", "price": "49000.00", "reference": None, "description_short": None},
      {"id_product": "42", "product_name": "Pantalón Gabardina", "category_name": "Gabardina Corte Chino.", "price": "89900.00", "reference": None, "description_short": None},
      {"id_product": "47", "product_name": "Camisas Sport con Bolsillo", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": "<p>Camisa clásica , algodón y polyester.</p>"},
      {"id_product": "49", "product_name": "Media Polera Algodón.", "category_name": "Polera Algodón.", "price": "19900.00", "reference": None, "description_short": "<p>Media Polera algodón.</p>"},
      {"id_product": "53", "product_name": "Jeans Rochas", "category_name": "Jean Gabardina.", "price": "120000.00", "reference": None, "description_short": "<p>Jeans.</p>"},
      {"id_product": "54", "product_name": "Remera Manga Larga", "category_name": "Remera M/L Lisa", "price": "20000.00", "reference": None, "description_short": "<p>Remera manga larga.</p>"},
      {"id_product": "55", "product_name": "Ambo", "category_name": "Ambo", "price": "590000.00", "reference": None, "description_short": None},
      {"id_product": "56", "product_name": "Chaleco Sport", "category_name": "Chaleco Mantelasse", "price": "39900.00", "reference": None, "description_short": "<p>Chaleco.</p>"},
      {"id_product": "57", "product_name": "Chomba Fantasia.", "category_name": "Remera M/L Fantasía.", "price": "42000.00", "reference": None, "description_short": "<p>Chomba algodón.</p>"},
      {"id_product": "58", "product_name": "Boxer", "category_name": "Bóxers", "price": "24900.00", "reference": None, "description_short": "<p>Boxers.</p>"},
      {"id_product": "59", "product_name": "Cintos.", "category_name": "Cintos", "price": "11900.00", "reference": None, "description_short": "<p>Cintos</p>"},
      {"id_product": "60", "product_name": "Jogger Gabardina discontinuos", "category_name": "Jogger Gabardina", "price": "29900.00", "reference": None, "description_short": "<p>Jogger gabardina.</p>"},
      {"id_product": "64", "product_name": "Camisa Lisa Clásica", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": "<p>Camisa Lisa Clasica.</p>"},
      {"id_product": "65", "product_name": "Camisa Lisa Slim", "category_name": "Camisas", "price": "90000.00", "reference": None, "description_short": "<p>Camisa Lisa</p>"},
      {"id_product": "67", "product_name": "7/8 Gabardina.", "category_name": "7/8 Gabardina", "price": "150000.00", "reference": None, "description_short": "<p>7/8 Gabardina.</p>"},
      {"id_product": "68", "product_name": "7/8 Paño.", "category_name": "7/8 Paño", "price": "150000.00", "reference": None, "description_short": "<p>7/8 Paño.</p>"},
      {"id_product": "69", "product_name": "Camisa Fantasía Slim", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": "<p>Camisa Slim</p>"},
      {"id_product": "70", "product_name": "Joggers Algodón.", "category_name": "Joggers Algodón Friza", "price": "21900.00", "reference": None, "description_short": None},
      {"id_product": "71", "product_name": "Poplin Chino", "category_name": "Poplin Chino", "price": "120000.00", "reference": None, "description_short": "<p>Pantalon Poplin corte chino</p>"},
      {"id_product": "74", "product_name": "Camisa Clásica Fantasia.", "category_name": "Corte Clásico", "price": "59000.00", "reference": None, "description_short": "<p>Camisa Fantasia clasica</p>"},
      {"id_product": "75", "product_name": "Camisa Lisa Vestir", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": "<p>Camisa Vestir</p>"},
      {"id_product": "78", "product_name": "Remeras manga corta", "category_name": "Remera M/C Lisa", "price": "20000.00", "reference": None, "description_short": "<p>Remera manga corta.</p>"},
      {"id_product": "79", "product_name": "Chomba Pique.", "category_name": "Inicio", "price": "69900.00", "reference": None, "description_short": "<p>Chomba Pique</p>"},
      {"id_product": "81", "product_name": "Bermuda Algodon", "category_name": "Bermudas", "price": "69000.00", "reference": None, "description_short": "<p>Bermuda algodón.</p>"},
      {"id_product": "82", "product_name": "Bermuda Gabardina", "category_name": "Bermudas", "price": "69000.00", "reference": None, "description_short": "<p>Bermuda Gabardina.</p>"},
      {"id_product": "83", "product_name": "Pantalón Lino.", "category_name": "Pantalón Lino", "price": "169000.00", "reference": None, "description_short": "<p>Pantalón Lino.</p>"},
      {"id_product": "89", "product_name": "Chomba Pique lisa", "category_name": "Chombas M/C", "price": "49900.00", "reference": None, "description_short": "<p>Chomba lisa pique</p>"},
      {"id_product": "91", "product_name": "Chomba pique", "category_name": "Chombas M/C", "price": "69900.00", "reference": None, "description_short": "<p>Chombas pique lisa</p>"},
      {"id_product": "92", "product_name": "Medias", "category_name": "Medias", "price": "24900.00", "reference": None, "description_short": "<p>Medias fantasia.</p>"},
      {"id_product": "93", "product_name": "Chombas de Jersey", "category_name": "Chombas M/C", "price": "79900.00", "reference": None, "description_short": "<p>Chombas jersey</p>"},
      {"id_product": "95", "product_name": "Chombas lisa Pique.", "category_name": "Chombas M/C", "price": "69900.00", "reference": None, "description_short": "<p>Chombas Pique</p>"},
      {"id_product": "98", "product_name": "Remera Lisa", "category_name": "Remera M/C Lisa", "price": "20000.00", "reference": None, "description_short": "<p>Remera lisa</p>"},
      {"id_product": "100", "product_name": "Camisa Manga Corta", "category_name": "Camisas", "price": "75000.00", "reference": None, "description_short": "<p>Camisa M/C Fantasia.</p>"},
      {"id_product": "102", "product_name": "Camisas Manga corta.", "category_name": "Camisas M/C", "price": "75000.00", "reference": None, "description_short": "<p>Camisas M/C Fantasía</p>"},
      {"id_product": "103", "product_name": "Camisas", "category_name": "Camisas", "price": "59000.00", "reference": None, "description_short": None},
      {"id_product": "104", "product_name": "Pulseras Simple cuero", "category_name": "Pulseras", "price": "10900.00", "reference": None, "description_short": "<p>Pulsera simple cuero.</p>"},
      {"id_product": "106", "product_name": "Pulsera Elastica Simple", "category_name": "Pulseras", "price": "12000.00", "reference": None, "description_short": "<p>Pulsera Elastica</p>"},
      {"id_product": "107", "product_name": "Pulsera doble piedras", "category_name": "Pulseras", "price": "15900.00", "reference": None, "description_short": "<p>Pulsera doble en piedras y cuero .</p>"},
      {"id_product": "108", "product_name": "Poleron", "category_name": "Polera Lana", "price": "90000.00", "reference": None, "description_short": "<p>Poleron de Lana</p>"},
      {"id_product": "110", "product_name": "Chaleco", "category_name": "Chaleco Algodon", "price": "145000.00", "reference": None, "description_short": "<p>Chaleco Algodon</p>"},
      {"id_product": "113", "product_name": "Saco sport pura lana", "category_name": "Saco Sport", "price": "490000.00", "reference": None, "description_short": "<p>Saco sport dos botones</p>"},
      {"id_product": "115", "product_name": "Suéter medio cierre merino", "category_name": "Sweaters", "price": "149000.00", "reference": None, "description_short": "<p>Suéter medio cierre .</p>"},
      {"id_product": "116", "product_name": "Campera algodón", "category_name": "Inicio", "price": "49000.00", "reference": None, "description_short": "<p>Campera algodón.</p>"},
      {"id_product": "117", "product_name": "Campera corta paño liso", "category_name": "Inicio", "price": "350000.00", "reference": None, "description_short": "<p>Campera paño corta liso .</p>"},
      {"id_product": "118", "product_name": "Campera micro polar", "category_name": "Inicio", "price": "120000.00", "reference": None, "description_short": "<p>Campera micro polar .</p>"},
      {"id_product": "119", "product_name": "Polerón pura lana .", "category_name": "Inicio", "price": "90000.00", "reference": None, "description_short": "<p>Polerón pura lana .</p>"},
      {"id_product": "120", "product_name": "Chomba manga larga", "category_name": "Inicio", "price": "42000.00", "reference": None, "description_short": "<p>Chomba manga larga lisa .</p>"},
      {"id_product": "121", "product_name": "Campera algodón .", "category_name": "Inicio", "price": "132000.00", "reference": None, "description_short": "<p>Campera algodón cuello universitario.</p>"},
      {"id_product": "125", "product_name": "Camisa Sport", "category_name": "Camisas", "price": "90000.00", "reference": None, "description_short": None},
      {"id_product": "127", "product_name": "Campera", "category_name": "campera paño", "price": "390000.00", "reference": None, "description_short": None},
      {"id_product": "128", "product_name": "campera lana", "category_name": "Campera Lana", "price": "145000.00", "reference": None, "description_short": None},
      {"id_product": "134", "product_name": "Chaleco", "category_name": "chaleco corderoy", "price": "150000.00", "reference": None, "description_short": None},
      {"id_product": "141", "product_name": "campera", "category_name": "campera paño", "price": "390000.00", "reference": None, "description_short": None},
      {"id_product": "143", "product_name": "campera", "category_name": "Campera Lana", "price": "110000.00", "reference": None, "description_short": None},
      {"id_product": "146", "product_name": "sweater", "category_name": "Sweaters", "price": "110000.00", "reference": None, "description_short": None},
      {"id_product": "147", "product_name": "camisa sport", "category_name": "Camisas", "price": "90000.00", "reference": None, "description_short": None},
      {"id_product": "148", "product_name": "campera impermeable", "category_name": "campera impermeable", "price": "153000.00", "reference": None, "description_short": None},
      {"id_product": "150", "product_name": "saco sport", "category_name": "Saco Sport", "price": "390000.00", "reference": None, "description_short": "<p>Saco sport doble bolsillo slim</p>"},
      {"id_product": "151", "product_name": "saco sport slim", "category_name": "Saco Sport", "price": "390000.00", "reference": None, "description_short": None},
      {"id_product": "152", "product_name": "saco sport", "category_name": "Saco Sport", "price": "390000.00", "reference": None, "description_short": "<p>Saco sport slim</p>"},
      {"id_product": "153", "product_name": "Ambo liso slim", "category_name": "Ambo", "price": "490000.00", "reference": None, "description_short": None},
      {"id_product": "155", "product_name": "Piloto", "category_name": "pilotin impermeable", "price": "450000.00", "reference": None, "description_short": "<p>pilotin impermeable 7/8.</p>"},
    ]

    variants_data = [
      {"id_product": "24", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "24", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "24", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "38", "attr_name": "Blanco", "attr_group": "color", "quantity": "5"},
      {"id_product": "38", "attr_name": "Celeste", "attr_group": "color", "quantity": "5"},
      {"id_product": "38", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "38", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "38", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "42", "attr_name": "Negro", "attr_group": "color", "quantity": "10"},
      {"id_product": "42", "attr_name": "Beige", "attr_group": "color", "quantity": "10"},
      {"id_product": "42", "attr_name": "Azul", "attr_group": "color", "quantity": "10"},
      {"id_product": "47", "attr_name": "Blanco", "attr_group": "color", "quantity": "10"},
      {"id_product": "47", "attr_name": "Negro", "attr_group": "color", "quantity": "10"},
      {"id_product": "47", "attr_name": "Azul", "attr_group": "color", "quantity": "10"},
      {"id_product": "53", "attr_name": "Gris", "attr_group": "color", "quantity": "10"},
      {"id_product": "53", "attr_name": "Azul", "attr_group": "color", "quantity": "10"},
      {"id_product": "53", "attr_name": "Negro", "attr_group": "color", "quantity": "10"},
      {"id_product": "54", "attr_name": "Negro", "attr_group": "color", "quantity": "10"},
      {"id_product": "54", "attr_name": "Gris pardo", "attr_group": "color", "quantity": "10"},
      {"id_product": "55", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "55", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "55", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "56", "attr_name": "Azul", "attr_group": "color", "quantity": "3"},
      {"id_product": "56", "attr_name": "Negro", "attr_group": "color", "quantity": "0"},
      {"id_product": "59", "attr_name": "Negro", "attr_group": "color", "quantity": "15"},
      {"id_product": "60", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "60", "attr_name": "Camel", "attr_group": "color", "quantity": "5"},
      {"id_product": "65", "attr_name": "Blanco", "attr_group": "color", "quantity": "20"},
      {"id_product": "67", "attr_name": "Negro", "attr_group": "color", "quantity": "0"},
      {"id_product": "67", "attr_name": "Beige", "attr_group": "color", "quantity": "2"},
      {"id_product": "68", "attr_name": "Beige", "attr_group": "color", "quantity": "3"},
      {"id_product": "70", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "70", "attr_name": "Verde", "attr_group": "color", "quantity": "5"},
      {"id_product": "70", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "71", "attr_name": "Camel", "attr_group": "color", "quantity": "5"},
      {"id_product": "71", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "75", "attr_name": "Rosa", "attr_group": "color", "quantity": "5"},
      {"id_product": "78", "attr_name": "Blanco", "attr_group": "color", "quantity": "5"},
      {"id_product": "78", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "78", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "79", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "79", "attr_name": "Rojo", "attr_group": "color", "quantity": "5"},
      {"id_product": "79", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "79", "attr_name": "Rosa", "attr_group": "color", "quantity": "5"},
      {"id_product": "81", "attr_name": "Blanco", "attr_group": "color", "quantity": "5"},
      {"id_product": "81", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "81", "attr_name": "Verde", "attr_group": "color", "quantity": "5"},
      {"id_product": "81", "attr_name": "Verde Militar", "attr_group": "color", "quantity": "5"},
      {"id_product": "82", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "82", "attr_name": "Beige", "attr_group": "color", "quantity": "5"},
      {"id_product": "83", "attr_name": "Beige", "attr_group": "color", "quantity": "5"},
      {"id_product": "89", "attr_name": "Celeste", "attr_group": "color", "quantity": "5"},
      {"id_product": "89", "attr_name": "Blanco", "attr_group": "color", "quantity": "5"},
      {"id_product": "89", "attr_name": "Rojo", "attr_group": "color", "quantity": "5"},
      {"id_product": "89", "attr_name": "Bordo", "attr_group": "color", "quantity": "5"},
      {"id_product": "89", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "91", "attr_name": "Rojo", "attr_group": "color", "quantity": "5"},
      {"id_product": "91", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "93", "attr_name": "Rojo", "attr_group": "color", "quantity": "5"},
      {"id_product": "93", "attr_name": "Blanco", "attr_group": "color", "quantity": "5"},
      {"id_product": "93", "attr_name": "Negro", "attr_group": "color", "quantity": "5"},
      {"id_product": "93", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "95", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "95", "attr_name": "Verde", "attr_group": "color", "quantity": "5"},
      {"id_product": "98", "attr_name": "Rosa", "attr_group": "color", "quantity": "5"},
      {"id_product": "98", "attr_name": "Amarillo", "attr_group": "color", "quantity": "5"},
      {"id_product": "98", "attr_name": "Celeste", "attr_group": "color", "quantity": "5"},
      {"id_product": "103", "attr_name": "Verde", "attr_group": "color", "quantity": "10"},
      {"id_product": "103", "attr_name": "Gris", "attr_group": "color", "quantity": "10"},
      {"id_product": "108", "attr_name": "Beige", "attr_group": "color", "quantity": "5"},
      {"id_product": "108", "attr_name": "Bordo", "attr_group": "color", "quantity": "5"},
      {"id_product": "110", "attr_name": "Bordo", "attr_group": "color", "quantity": "5"},
      {"id_product": "110", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "113", "attr_name": "Gris", "attr_group": "color", "quantity": "5"},
      {"id_product": "117", "attr_name": "Camel", "attr_group": "color", "quantity": "2"},
      {"id_product": "117", "attr_name": "Negro", "attr_group": "color", "quantity": "0"},
      {"id_product": "118", "attr_name": "Gris", "attr_group": "color", "quantity": "4"},
      {"id_product": "118", "attr_name": "Azul", "attr_group": "color", "quantity": "4"},
      {"id_product": "119", "attr_name": "Bordo", "attr_group": "color", "quantity": "5"},
      {"id_product": "119", "attr_name": "Beige", "attr_group": "color", "quantity": "5"},
      {"id_product": "119", "attr_name": "Gris pardo", "attr_group": "color", "quantity": "5"},
      {"id_product": "120", "attr_name": "Azul", "attr_group": "color", "quantity": "5"},
      {"id_product": "120", "attr_name": "Verde", "attr_group": "color", "quantity": "5"},
      {"id_product": "120", "attr_name": "Celeste", "attr_group": "color", "quantity": "5"},
      {"id_product": "121", "attr_name": "Azul", "attr_group": "color", "quantity": "3"},
      {"id_product": "121", "attr_name": "Gris pardo", "attr_group": "color", "quantity": "3"}
    ]

    # 1. Asegurar que existan Categorías
    cat_map = {}
    for p in products_data:
        cat_name = p['category_name']
        if cat_name and cat_name not in cat_map:
            cat, created = Categoria.objects.get_or_create(nombre=cat_name)
            cat_map[cat_name] = cat

    # 2. Asegurar que existan Colores
    color_map = {}
    for v in variants_data:
        if v['attr_group'] == 'color':
            color_name = v['attr_name']
            if color_name not in color_map:
                color, created = Color.objects.get_or_create(nombre=color_name)
                color_map[color_name] = color

    # 3. Asegurar que exista al menos un Talle por defecto (U para Único o S/M/L)
    # PrestaShop no me devolvió los talles en la consulta rápida, así que usaré 'U' por ahora
    talle_u, _ = Talle.objects.get_or_create(nombre='Único', abbreviation='U')

    # 4. Crear Productos
    for p_data in products_data:
        p_id = p_data['id_product']
        try:
            prod, created = Producto.objects.update_or_create(
                id=int(p_id),
                defaults={
                    'nombre': p_data['product_name'],
                    'descripcion': p_data['description_short'] or p_data['product_name'],
                    'precio': float(p_data['price']),
                    'categoria': cat_map[p_data['category_name']]
                }
            )
            
            # 5. Crear Stock para las variantes de este producto
            prod_variants = [v for v in variants_data if v['id_product'] == p_id]
            
            for v in prod_variants:
                if v['attr_group'] == 'color':
                    color_obj = color_map[v['attr_name']]
                    # Agregamos el color a la relación ManyToMany
                    prod.colores.add(color_obj)
                    
                    # Creamos la entrada en ProductoStock
                    # Como no tenemos talles mapeados, usamos el Talle Único por ahora
                    ProductoStock.objects.update_or_create(
                        producto=prod,
                        color=color_obj,
                        talle=talle_u,
                        defaults={'stock': int(v['quantity'])}
                    )
            
            print(f"Migrado: {prod.nombre}")
        except Exception as e:
            print(f"Error migrando producto {p_id}: {e}")

if __name__ == "__main__":
    migrate_data()
