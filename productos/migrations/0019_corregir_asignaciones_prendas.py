from django.db import migrations


def corregir_asignaciones(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    database = schema_editor.connection.alias

    campera_polar = Categoria.objects.using(database).get(nombre="Campera Polar")
    chombas = Categoria.objects.using(database).get(nombre="Chombas")

    Producto.objects.using(database).filter(codigo="001016").update(
        categoria_id=campera_polar.pk,
    )
    Producto.objects.using(database).filter(
        nombre__iexact="Chomba Fantasia.",
    ).update(categoria_id=chombas.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0018_normalizar_nombres_categorias"),
    ]

    operations = [
        migrations.RunPython(corregir_asignaciones, migrations.RunPython.noop),
    ]
