from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections, transaction
from django.db.models import Exists, OuterRef, Sum

from productos.models import (
    Categoria,
    Color,
    Estilo,
    Marca,
    Producto,
    ProductoStock,
    Talle,
    Tipo,
)


class Command(BaseCommand):
    help = 'Replace the Supabase catalog and stock from a Django fixture.'

    def add_arguments(self, parser):
        parser.add_argument('fixture')
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of the current catalog before importing.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError(
                'This replaces catalog data. Re-run with --confirm only '
                'after verifying the target database.'
            )
        if connections['default'].vendor != 'postgresql':
            raise CommandError(
                'Refusing to replace the catalog unless the default database '
                'is PostgreSQL.'
            )

        fixture = Path(options['fixture'])
        if not fixture.is_file():
            raise CommandError(f'Fixture not found: {fixture}')

        with transaction.atomic():
            ProductoStock.objects.all().delete()
            Producto.objects.all().delete()
            for model in (Color, Talle, Marca, Estilo, Tipo, Categoria):
                model.objects.all().delete()

            call_command(
                'loaddata',
                str(fixture),
                database='default',
                verbosity=0,
            )
            Producto.objects.update(
                esta_activo=Exists(
                    ProductoStock.objects.filter(
                        producto_id=OuterRef('pk'),
                        stock__gt=0,
                    )
                )
            )

        total_products = Producto.objects.count()
        active_products = Producto.objects.filter(esta_activo=True).count()
        variant_count = ProductoStock.objects.count()
        units = ProductoStock.objects.aggregate(total=Sum('stock'))['total'] or 0
        self.stdout.write(
            self.style.SUCCESS(
                f'Replaced catalog: {total_products} products, '
                f'{active_products} active, {variant_count} stock variants, '
                f'{units} units.'
            )
        )
