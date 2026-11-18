from django.db import migrations


RENOMBRES = {
    "campera pa\u00f1o": "Campera Pa\u00f1o",
    "chaleco corderoy": "Chaleco Corderoy",
    "campera impermeable": "Campera Impermeable",
    "pilotin impermeable": "Pilot\u00edn Impermeable",
    "Jean Gabardina.": "Jean Gabardina",
    "7/8 Pa\u00f1o": "7/8 Pa\u00f1o",
}


CATEGORIAS_PADRES = {
    "Camisas": ["Camisas M/C", "Corte Cl\u00e1sico"],
    "Remeras": ["Remera M/C Lisa", "Remera M/L Lisa", "Remera M/L Fantas\u00eda."],
    "Chombas": ["Chombas M/C", "Chombas M/L"],
    "Pantalones": [
        "7/8 Gabardina", "7/8 Pa\u00f1o", "7/8 Lana", "Bermudas",
        "Gabardina Corte Chino.", "Jeans", "Jogger Gabardina",
        "Joggers Algod\u00f3n Friza", "Pantal\u00f3n Lino", "Poplin Chino",
    ],
    "Jeans": ["Jean Lona", "Jean Gabardina", "Jean Corderoy"],
    "Camperas": [
        "Campera Algod\u00f3n", "Campera Lana", "Campera Pa\u00f1o",
        "Campera Impermeable", "Campera Polar", "Pilot\u00edn Impermeable",
    ],
    "Chalecos": ["Chaleco Algodon", "Chaleco Mantelasse", "Chaleco Corderoy"],
    "Sweaters": ["Polera Algod\u00f3n.", "Polera Lana"],
    "Sacos/Blazers": ["Saco Sport"],
    "Ambos": ["Ambo"],
    "Accesorios": [
        "Cintos", "Corbatas", "Gemelos/Mancuernillas",
        "Pa\u00f1uelos de bolsillo", "Pisa corbata/Pasador", "Pulseras",
    ],
    "Ropa Interior": ["B\u00f3xers", "Medias"],
    "Regalos": ["Gift Cards", "Kits de Regalo"],
}


PRODUCTOS_INICIO = {
    "Campera algod\u00f3n": "Campera Algod\u00f3n",
    "Campera algod\u00f3n .": "Campera Algod\u00f3n",
    "Campera corta pa\u00f1o liso": "Campera Pa\u00f1o",
    "Campera micro polar": "Campera Polar",
    "Chomba Pique.": "Chombas M/C",
    "Chomba manga larga": "Chombas M/L",
    "Poler\u00f3n pura lana .": "Polera Lana",
}


def ordenar_categorias(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    database = schema_editor.connection.alias

    categorias = {
        categoria.nombre: categoria
        for categoria in Categoria.objects.using(database).all()
    }

    for nombre_actual, nombre_nuevo in RENOMBRES.items():
        categoria = categorias.get(nombre_actual)
        if categoria and nombre_actual != nombre_nuevo:
            conflicto = Categoria.objects.using(database).filter(
                nombre=nombre_nuevo,
            ).exclude(pk=categoria.pk).exists()
            if conflicto:
                raise RuntimeError(
                    f"No se puede renombrar {nombre_actual!r}: "
                    f"ya existe {nombre_nuevo!r}."
                )
            categoria.nombre = nombre_nuevo
            categoria.save(update_fields=["nombre"])
            categorias.pop(nombre_actual)
            categorias[nombre_nuevo] = categoria

    nuevos_nombres = {
        nombre
        for nombre in CATEGORIAS_PADRES
        if nombre not in categorias
    }
    nuevos_nombres.update(
        nombre
        for nombres_hijos in CATEGORIAS_PADRES.values()
        for nombre in nombres_hijos
        if nombre not in categorias
    )
    for nombre in sorted(nuevos_nombres):
        categoria, _ = Categoria.objects.using(database).get_or_create(
            nombre=nombre,
            defaults={"descripcion": ""},
        )
        categorias[nombre] = categoria

    nombres = set(categorias)
    for padre, hijos in CATEGORIAS_PADRES.items():
        if padre not in nombres or not set(hijos).issubset(nombres):
            raise RuntimeError(f"Falta una categoría necesaria para {padre!r}.")

    padres_de_hijos = {
        hijo: padre
        for padre, hijos in CATEGORIAS_PADRES.items()
        for hijo in hijos
    }
    if len(padres_de_hijos) != sum(map(len, CATEGORIAS_PADRES.values())):
        raise RuntimeError("Una categoría quedó asignada a más de un padre.")

    for categoria in categorias.values():
        nombre_padre = padres_de_hijos.get(categoria.nombre)
        parent_id = categorias[nombre_padre].pk if nombre_padre else None
        if categoria.parent_id != parent_id:
            categoria.parent_id = parent_id
            categoria.save(update_fields=["parent"])

    camperas = categorias["Camperas"]
    Producto.objects.using(database).filter(
        nombre__iexact="Campera",
        categoria__nombre__in=["Campera Pa\u00f1o", "Campera Lana"],
    ).update(categoria_id=camperas.pk)

    codigo_lana = Producto.objects.using(database).filter(codigo="001088")
    lana_categoria = categorias["7/8 Lana"]
    codigo_lana.update(categoria_id=lana_categoria.pk)

    for nombre_producto, nombre_categoria in PRODUCTOS_INICIO.items():
        producto = Producto.objects.using(database).filter(
            nombre=nombre_producto,
            categoria__nombre="Inicio",
        )
        producto.update(categoria_id=categorias[nombre_categoria].pk)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0015_categorizar_articulos_excel"),
    ]

    operations = [
        migrations.RunPython(ordenar_categorias, migrations.RunPython.noop),
    ]
