from django.db import migrations


def eliminar_inicio_si_vacia(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Producto = apps.get_model("productos", "Producto")
    database = schema_editor.connection.alias

    categorias_inicio = Categoria.objects.using(database).filter(nombre="Inicio")
    for categoria in categorias_inicio:
        tiene_productos = Producto.objects.using(database).filter(
            categoria_id=categoria.pk,
        ).exists()
        tiene_subcategorias = Categoria.objects.using(database).filter(
            parent_id=categoria.pk,
        ).exists()
        if tiene_productos or tiene_subcategorias:
            raise RuntimeError(
                "No se puede eliminar la categoría 'Inicio': "
                "todavía tiene productos o subcategorías asignados."
            )
        categoria.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0019_corregir_asignaciones_prendas"),
    ]

    operations = [
        migrations.RunPython(eliminar_inicio_si_vacia, migrations.RunPython.noop),
    ]
