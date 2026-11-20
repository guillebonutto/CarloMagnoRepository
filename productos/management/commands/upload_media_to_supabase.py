from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError

from productos.models import Marca, Producto


class Command(BaseCommand):
    help = 'Upload referenced local product and brand images to Supabase Storage.'

    def handle(self, *args, **options):
        storage_config = settings.STORAGES['default']
        if (
            storage_config['BACKEND']
            != 'django_supabase_storage.SupabaseMediaStorage'
        ):
            raise CommandError(
                'Configure Supabase Storage before uploading media.'
            )

        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        media_fields = (
            (Producto, 'imagen'),
            (Marca, 'logo'),
        )
        saved_names = {}
        missing_names = set()

        for model, field_name in media_fields:
            references = (
                model.objects.exclude(**{field_name: ''})
                .values_list(field_name, flat=True)
                .distinct()
            )
            for name in references.iterator():
                if not name:
                    continue
                if name in saved_names:
                    saved_name = saved_names[name]
                    if saved_name != name:
                        model.objects.filter(**{field_name: name}).update(
                            **{field_name: saved_name}
                        )
                    continue
                try:
                    with local_storage.open(name, 'rb') as source:
                        saved_name = default_storage.save(name, File(source))
                except FileNotFoundError:
                    missing_names.add(name)
                    continue

                if saved_name != name:
                    model.objects.filter(**{field_name: name}).update(
                        **{field_name: saved_name}
                    )
                saved_names[name] = saved_name

        self.stdout.write(
            self.style.SUCCESS(
                f'Uploaded {len(saved_names)} referenced files to Supabase.'
            )
        )
        if missing_names:
            missing_list = ', '.join(sorted(missing_names))
            self.stderr.write(
                self.style.WARNING(
                    f'{len(missing_names)} local files were not found: '
                    f'{missing_list}'
                )
            )
