import re
import unicodedata

from django.db import migrations


MARCAS = (
    (
        "Yves Saint Laurent",
        (r"\byves\s+saint\s+laurent\b", r"\bysl\b"),
    ),
    ("Pierre Cardin", (r"\bpierre\s+cardin\b",)),
    ("Rochas Paris", (r"\brochas(?:\s+paris)?\b",)),
    ("Christian Lacroix", (r"\b(?:christian\s+)?lacroix\b",)),
    ("Dior", (r"\bdior\b",)),
    ("New Bredy", (r"\bnew\s+bredy\b",)),
)


def normalizar(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(caracter)
    )


def quitar_marcas_de_nombres(apps, database):
    Producto = apps.get_model("productos", "Producto")
    Marca = apps.get_model("productos", "Marca")
    marcas = {}

    for nombre, patrones in MARCAS:
        marca = Marca.objects.using(database).filter(nombre__iexact=nombre).first()
        if marca is None:
            marca = Marca.objects.using(database).create(nombre=nombre)
        marcas[nombre] = (marca, tuple(re.compile(patron, re.IGNORECASE) for patron in patrones))

    productos = Producto.objects.using(database).filter(nombre__icontains="(ver)")
    for producto in productos.iterator(chunk_size=200):
        if not producto.nombre.rstrip().casefold().endswith("(ver)"):
            continue

        coincidencias = [
            (nombre, marca, patrones)
            for nombre, (marca, patrones) in marcas.items()
            if any(patron.search(producto.nombre) for patron in patrones)
        ]
        if not coincidencias:
            continue
        if len(coincidencias) > 1:
            raise RuntimeError(
                f"El producto {producto.codigo!r} coincide con varias marcas."
            )

        _, marca, patrones = coincidencias[0]
        nombre = producto.nombre
        for patron in patrones:
            nombre = patron.sub(" ", nombre)
        nombre = re.sub(r"\s+", " ", nombre)
        nombre = re.sub(r"\s+([,.;:])", r"\1", nombre).strip(" \t,;:")

        producto.nombre = nombre
        producto.marca_id = marca.pk
        producto.save(using=database, update_fields=["nombre", "marca"])


def obtener_categoria(apps, database, nombre, parent_id):
    Categoria = apps.get_model("productos", "Categoria")
    categoria, _ = Categoria.objects.using(database).get_or_create(
        nombre=nombre,
        parent_id=parent_id,
        defaults={"descripcion": ""},
    )
    return categoria


def renombrar_categoria(apps, database, padre, nombre_actual, nombre_nuevo):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    categoria_actual = Categoria.objects.using(database).filter(
        nombre=nombre_actual,
        parent_id=padre.pk,
    ).first()
    categoria_nueva = Categoria.objects.using(database).filter(
        nombre=nombre_nuevo,
        parent_id=padre.pk,
    ).first()

    if categoria_actual is None:
        return categoria_nueva or obtener_categoria(
            apps, database, nombre_nuevo, padre.pk,
        )
    if categoria_nueva is None:
        categoria_actual.nombre = nombre_nuevo
        categoria_actual.save(update_fields=["nombre"])
        return categoria_actual

    Producto.objects.using(database).filter(
        categoria_id=categoria_actual.pk,
    ).update(categoria_id=categoria_nueva.pk)
    Categoria.objects.using(database).filter(
        parent_id=categoria_actual.pk,
    ).update(parent_id=categoria_nueva.pk)
    categoria_actual.delete()
    return categoria_nueva


def asignar_subcategorias_chombas(apps, database):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    chombas = Categoria.objects.using(database).filter(
        nombre="Chombas",
        parent_id__isnull=True,
    ).first()
    if chombas is None:
        return

    mangas = {
        "Manga corta": renombrar_categoria(
            apps, database, chombas, "Chombas M/C", "Manga corta",
        ),
        "Manga larga": renombrar_categoria(
            apps, database, chombas, "Chombas M/L", "Manga larga",
        ),
        "Manga no especificada": obtener_categoria(
            apps, database, "Manga no especificada", chombas.pk,
        ),
    }

    ramas = [chombas.pk] + [categoria.pk for categoria in mangas.values()]
    productos = (
        Producto.objects.using(database)
        .filter(categoria_id__in=ramas)
        .select_related("categoria")
    )

    for producto in productos.iterator(chunk_size=200):
        nombre_normalizado = normalizar(producto.nombre)
        categoria_actual = producto.categoria
        nombre_categoria = normalizar(categoria_actual.nombre)

        if categoria_actual.pk == mangas["Manga corta"].pk:
            manga = "Manga corta"
        elif categoria_actual.pk == mangas["Manga larga"].pk:
            manga = "Manga larga"
        elif "manga larga" in nombre_normalizado:
            manga = "Manga larga"
        elif "manga corta" in nombre_normalizado:
            manga = "Manga corta"
        elif "m/c" in nombre_categoria:
            manga = "Manga corta"
        elif "m/l" in nombre_categoria:
            manga = "Manga larga"
        else:
            manga = "Manga no especificada"

        tiene_pique = "pique" in nombre_normalizado or "piquet" in nombre_normalizado
        tiene_lisa = "lisa" in nombre_normalizado
        if tiene_pique and tiene_lisa:
            estilo = "Piqué liso"
        elif tiene_pique:
            estilo = "Piqué"
        elif "baston" in nombre_normalizado:
            estilo = "Bastón"
        elif "jersey" in nombre_normalizado or "yersey" in nombre_normalizado:
            estilo = "Jersey"
        elif tiene_lisa:
            estilo = "Lisa"
        elif "fantasia" in nombre_normalizado:
            estilo = "Fantasía"
        else:
            estilo = "Otros"

        categoria_manga = mangas[manga]
        categoria_estilo = obtener_categoria(
            apps, database, estilo, categoria_manga.pk,
        )
        if producto.categoria_id != categoria_estilo.pk:
            producto.categoria_id = categoria_estilo.pk
            producto.save(using=database, update_fields=["categoria"])


def normalizar_catalogo(apps, schema_editor):
    database = schema_editor.connection.alias
    quitar_marcas_de_nombres(apps, database)
    asignar_subcategorias_chombas(apps, database)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0022_mover_atributos_a_variantes"),
    ]

    operations = [
        migrations.RunPython(
            normalizar_catalogo,
            migrations.RunPython.noop,
        ),
    ]
