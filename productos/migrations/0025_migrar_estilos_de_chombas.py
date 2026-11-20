from django.db import migrations


def migrate_chomba_styles(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Estilo = apps.get_model("productos", "Estilo")
    Producto = apps.get_model("productos", "Producto")
    database = schema_editor.connection.alias

    chombas = Categoria.objects.using(database).filter(
        nombre="Chombas",
        parent_id__isnull=True,
    ).first()
    if chombas is None:
        return

    manga_categories = Categoria.objects.using(database).filter(
        parent_id=chombas.pk,
    )
    for manga in manga_categories:
        style_categories = list(
            Categoria.objects.using(database).filter(parent_id=manga.pk)
        )
        for style_category in style_categories:
            has_children = Categoria.objects.using(database).filter(
                parent_id=style_category.pk,
            ).exists()
            if has_children:
                raise RuntimeError(
                    f"La categoría de estilo {style_category.nombre!r} "
                    "tiene subcategorías y no se puede migrar automáticamente."
                )

            estilo, _ = Estilo.objects.using(database).get_or_create(
                nombre=style_category.nombre,
                defaults={
                    "order": style_category.pk,
                    "esta_activo": True,
                },
            )
            Producto.objects.using(database).filter(
                categoria_id=style_category.pk,
            ).update(
                categoria_id=manga.pk,
                estilo_id=estilo.pk,
            )
            style_category.delete(using=database)

    for name in ("Manga corta", "Manga larga"):
        Estilo.objects.using(database).get_or_create(
            nombre=name,
            defaults={"order": 0, "esta_activo": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0024_estilo_producto_estilo"),
    ]

    operations = [
        migrations.RunPython(
            migrate_chomba_styles,
            migrations.RunPython.noop,
        ),
    ]
