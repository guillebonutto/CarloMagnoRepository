from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0021_crear_variantes_stock_existentes"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="producto",
            name="colores",
        ),
        migrations.RemoveField(
            model_name="producto",
            name="talle",
        ),
    ]
