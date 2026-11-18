from decimal import Decimal

from django.db import migrations


ARTICULOS = [
    ("001088", "7/8 Pura lana peinada", "790000"),
    ("001019", "Ambo liso importado", "490000"),
    ("001080", "Ambo liso regular", "490000"),
    ("001089", "Ambo recto importado", "490000"),
    ("001074", "Ambo rochas", "650000"),
    ("001083", "Ambo zolapa raso", "990000"),
    ("001087", "Articulo Promocion", "190000"),
    ("001081", "Bermuda gabardina lisa", "85000"),
    ("001082", "Bermuda jeans", "85000"),
    ("001072", "Bermudas", "0"),
    ("001061", "Boxer ysl", "24900"),
    ("001041", "Buzo fsia ysl con cuello 4", "89000"),
    ("001018", "Buzo Liso ysl", "69000"),
    ("001040", "Camisa corderoy ysl", "110000"),
    ("001057", "Camisa doble pu\u00f1o", "120000"),
    ("001084", "Camisa Lino regular ysl", "110000"),
    ("001003", "Camisa Lisa Vestir pierre cardin slim", "90000"),
    ("001069", "Camisa mangas cortas", "89000"),
    ("001079", "Camisa mao ysl", "90000"),
    ("001002", "Camisa sport manga larga", "90000"),
    ("001075", "Camisa sport sin bolsillo", "90000"),
    ("001026", "Camisa Vestir Rochas Fantasia", "129900"),
    ("001055", "Camisa vestir ysl", "90000"),
    ("001025", "Camisa vestir ysl lisa", "90000"),
    ("001073", "Camisa ysl regular vestir", "110000"),
    ("001053", "Camisaco rochas pa\u00f1o", "390000"),
    ("001050", "Camisas ysl not aegean", "99000"),
    ("001007", "Campera Algodon Lacroix", "49000"),
    ("001058", "Campera bomber rochas", "490000"),
    ("001066", "Campera canelon rochas", "170000"),
    ("001015", "Campera de Pa\u00f1o Rochas", "0"),
    ("001010", "Campera Mezcla", "0"),
    ("001016", "Campera Polar Ysl", "149000"),
    ("001065", "Campera sofshell", "180000"),
    ("001045", "Cardigan boton pierre cardin", "136000"),
    ("001051", "Chaleco corderoy rochas", "190000"),
    ("001027", "Chaleco Pierre Cardin Merino", "0"),
    ("001077", "Chomba  baston algodon", "89000"),
    ("001067", "Chomba piquet", "79000"),
    ("001068", "Chomba yersey algodon", "79000"),
    ("001054", "Chombas varias manga larga", "39000"),
    ("001064", "Cinto sport pierre cardin", "490000"),
    ("001091", "Cinturon vestir importado", "69000"),
    ("001056", "corbatas", "50000"),
    ("001033", "Gabardina cargo pierre cardin", "90000"),
    ("001034", "Jean 5 bolsillos rochas", "129000"),
    ("001014", "Jean Pierre Cardin 5 Bolsillos", "90000"),
    ("001059", "Jeans corderoy pierre cardin", "125000"),
    ("001085", "Jeans Dior", "99000"),
    ("0010141", "jeans rochas", "129000"),
    ("001062", "Media vestir pierre cardin", "15000"),
    ("001009", "Medio Cierre Merino", "139000"),
    ("001035", "Pantalon Cargo Pierre Cardin Clasico", "0"),
    ("001086", "pantalon chino dior", "110000"),
    ("001090", "Pantalon chino importado", "0"),
    ("001032", "Pantalon Gabardina New Bredy", "129000"),
    ("001031", "Pantalon Gabardina Pierre Cardin", "90000"),
    ("001030", "Pantalon Gabardina Rochas Corte Chino", "139000"),
    ("001060", "Pantalon vestir", "90000"),
    ("001028", "Pantalon vestir rochas", "169000"),
    ("001052", "Pilotin pioggia rochas", "450000"),
    ("001005", "Poleron Pierre Cardin", "0"),
    ("001042", "Remera manga larga algodon ysl", "49900"),
    ("001043", "Remera manga larga piquet ysl", "69900"),
    ("001070", "remeras mangas cortas rochas", "49000"),
    ("001022", "Saco Pierre Cardin", "390000"),
    ("001020", "Saco Pura Lana Rochas", "0"),
    ("001023", "Saco Sport", "290000"),
    ("001078", "saco sport lino rochas", "550000"),
    ("001038", "Saco Sport rochas", "390000"),
    ("001012", "Sueter Cuello Base Lana", "110000"),
    ("001011", "Sueter Medio Cierre Lana", "110000"),
    ("001047", "sweters bremer rochas angora", "149000"),
    ("001048", "sweters cuello fumador rochas", "145000"),
    ("001044", "sweters cuello redondo pierre cardin", "102000"),
    ("001046", "sweters medio cierre pierre cardin", "130000"),
    ("001049", "swetwrs bossa rochas cuello base", "117000"),
]


def importar_articulos(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")

    for codigo, nombre, precio in ARTICULOS:
        nombre_marcado = f"{nombre} (ver)"
        producto, creado = Producto.objects.using(schema_editor.connection.alias).get_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre_marcado,
                "descripcion": nombre,
                "precio": Decimal(precio),
                "esta_activo": False,
            },
        )
        if not creado and (
            producto.nombre != nombre_marcado
            or producto.precio != Decimal(precio)
            or producto.esta_activo
        ):
            raise RuntimeError(
                f"El código de artículo {codigo} ya existe con datos diferentes."
            )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0013_producto_codigo"),
    ]

    operations = [
        migrations.RunPython(importar_articulos, migrations.RunPython.noop),
    ]
