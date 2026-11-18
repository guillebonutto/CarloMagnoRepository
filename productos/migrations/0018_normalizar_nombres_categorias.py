from django.db import migrations


RENOMBRES = {
    "Chaleco Algodon": "Chaleco Algod\u00f3n",
    "Gabardina Corte Chino.": "Gabardina Corte Chino",
    "Polera Algod\u00f3n.": "Polera Algod\u00f3n",
    "Remera M/L Fantas\u00eda.": "Remera M/L Fantas\u00eda",
}


def normalizar_nombres(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    database = schema_editor.connection.alias

    for nombre_actual, nombre_nuevo in RENOMBRES.items():
        categoria = Categoria.objects.using(database).filter(
            nombre=nombre_actual,
        ).first()
        if categoria is None:
            continue
        if Categoria.objects.using(database).filter(
            nombre=nombre_nuevo,
        ).exclude(pk=categoria.pk).exists():
            raise RuntimeError(
                f"No se puede renombrar {nombre_actual!r}: "
                f"ya existe {nombre_nuevo!r}."
            )
        categoria.nombre = nombre_nuevo
        categoria.save(update_fields=["nombre"])


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0017_corregir_categoria_camisaco"),
    ]

    operations = [
        migrations.RunPython(normalizar_nombres, migrations.RunPython.noop),
    ]
