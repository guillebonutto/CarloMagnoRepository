from django.db import migrations


CATEGORIAS_ARTICULOS = {
    "7/8 Pa\u00f1o": ["001088"],
    "Ambo": ["001019", "001080", "001089", "001074", "001083"],
    "Promociones": ["001087"],
    "Bermudas": ["001081", "001082", "001072"],
    "B\u00f3xers": ["001061"],
    "Buzos": ["001041", "001018"],
    "Camisas": [
        "001040", "001057", "001084", "001003", "001079", "001002",
        "001075", "001026", "001055", "001025", "001073", "001050",
    ],
    "Camisas M/C": ["001069"],
    "campera pa\u00f1o": ["001053", "001015"],
    "Campera Algod\u00f3n": ["001007"],
    "Camperas": ["001058", "001066", "001010", "001065"],
    "Campera Lana": ["001016"],
    "Sweaters": ["001045", "001009", "001012", "001011", "001047", "001048", "001044", "001046", "001049"],
    "chaleco corderoy": ["001051"],
    "Chalecos": ["001027"],
    "Chombas": ["001077", "001054"],
    "Chombas M/C": ["001067", "001068"],
    "Cintos": ["001064", "001091"],
    "Corbatas": ["001056"],
    "Pantalones": ["001033", "001035", "001060", "001028"],
    "Jean Lona": ["001034", "001014", "001085"],
    "Jean Corderoy": ["001059"],
    "Jean Gabardina.": ["0010141"],
    "Medias": ["001062"],
    "Poplin Chino": ["001086", "001090"],
    "Gabardina Corte Chino.": ["001032", "001031", "001030"],
    "pilotin impermeable": ["001052"],
    "Polera Lana": ["001005"],
    "Remera M/L Lisa": ["001042", "001043"],
    "Remera M/C Lisa": ["001070"],
    "Sacos/Blazers": ["001022", "001020"],
    "Saco Sport": ["001023", "001078", "001038"],
}


def categorizar_articulos(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    Categoria = apps.get_model("productos", "Categoria")
    database = schema_editor.connection.alias

    codigos = [
        codigo
        for codigos_categoria in CATEGORIAS_ARTICULOS.values()
        for codigo in codigos_categoria
    ]
    if len(codigos) != len(set(codigos)):
        raise RuntimeError("Hay códigos asignados a más de una categoría.")

    productos = Producto.objects.using(database).in_bulk(codigos, field_name="codigo")
    faltantes = sorted(set(codigos) - set(productos))
    if faltantes:
        raise RuntimeError(f"No se encontraron los artículos: {', '.join(faltantes)}")

    categorias = {}
    for nombre in CATEGORIAS_ARTICULOS:
        categorias[nombre], _ = Categoria.objects.using(database).get_or_create(
            nombre=nombre,
            defaults={"descripcion": ""},
        )

    for nombre, codigos_categoria in CATEGORIAS_ARTICULOS.items():
        ids = [productos[codigo].pk for codigo in codigos_categoria]
        Producto.objects.using(database).filter(pk__in=ids).update(
            categoria_id=categorias[nombre].pk,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0014_importar_articulos_excel"),
    ]

    operations = [
        migrations.RunPython(categorizar_articulos, migrations.RunPython.noop),
    ]
