from django.db import migrations


TIPOS_DE_TELA = (
    "Piqué",
    "Piqué liso",
    "Jersey",
    "Bastón",
    "Fantasía",
    "Otros",
)

ESTILOS = (
    "Clásico",
    "Casual",
    "Deportivo",
    "Corporativo",
)


def separar_estilo_y_tipo(apps, schema_editor):
    Estilo = apps.get_model("productos", "Estilo")
    Producto = apps.get_model("productos", "Producto")
    Tipo = apps.get_model("productos", "Tipo")
    database = schema_editor.connection.alias

    for nombre_tipo in TIPOS_DE_TELA:
        estilo_anterior = Estilo.objects.using(database).filter(
            nombre__iexact=nombre_tipo,
        ).first()
        defaults = {
            "order": estilo_anterior.order if estilo_anterior else 0,
            "esta_activo": estilo_anterior.esta_activo if estilo_anterior else True,
        }
        tipo, _ = Tipo.objects.using(database).get_or_create(
            nombre=nombre_tipo,
            defaults=defaults,
        )
        if estilo_anterior is not None:
            Producto.objects.using(database).filter(
                estilo_id=estilo_anterior.pk,
            ).update(
                tipo_id=tipo.pk,
                estilo_id=None,
            )
            estilo_anterior.delete(using=database)

    for nombre_estilo in ESTILOS:
        Estilo.objects.using(database).get_or_create(
            nombre=nombre_estilo,
            defaults={"order": 0, "esta_activo": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0026_tipo_producto_tipo"),
    ]

    operations = [
        migrations.RunPython(
            separar_estilo_y_tipo,
            migrations.RunPython.noop,
        ),
    ]
