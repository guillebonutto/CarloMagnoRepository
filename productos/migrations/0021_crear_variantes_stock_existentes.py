from django.db import migrations


def crear_variantes_stock_existentes(apps, schema_editor):
    Producto = apps.get_model("productos", "Producto")
    ProductoStock = apps.get_model("productos", "ProductoStock")
    database = schema_editor.connection.alias

    productos = (
        Producto.objects.using(database)
        .filter(talle__isnull=False)
        .prefetch_related("colores")
    )
    for producto in productos.iterator(chunk_size=200):
        for color in producto.colores.all():
            ProductoStock.objects.using(database).get_or_create(
                producto_id=producto.pk,
                color_id=color.pk,
                talle_id=producto.talle_id,
                defaults={"stock": 0},
            )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0020_eliminar_categoria_inicio"),
    ]

    operations = [
        migrations.RunPython(
            crear_variantes_stock_existentes,
            migrations.RunPython.noop,
        ),
    ]
