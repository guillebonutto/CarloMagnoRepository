from django.db import migrations


def corregir_categoria_camisaco(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    database = schema_editor.connection.alias

    camisas = Categoria.objects.using(database).get(nombre="Camisas")
    Producto.objects.using(database).filter(codigo="001053").update(
        categoria_id=camisas.pk,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0016_ordenar_jerarquia_categorias"),
    ]

    operations = [
        migrations.RunPython(corregir_categoria_camisaco, migrations.RunPython.noop),
    ]
