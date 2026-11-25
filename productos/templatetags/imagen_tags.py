from django import template
from django.conf import settings

register = template.Library()


@register.filter
def imagen_url(imagen):
    """Devuelve la URL pública de una imagen sin inicializar el cliente de Storage.

    ``FieldFile.url`` llama al storage, y el storage de Supabase crea un cliente
    con una llamada de red la primera vez. Para solo mostrar URLs alcanza con
    armar la dirección pública a partir de los settings.
    """
    name = imagen if isinstance(imagen, str) else getattr(imagen, 'name', '')
    if not name:
        return ''

    backend = settings.STORAGES.get('default', {}).get('BACKEND', '')
    if backend == 'django_supabase_storage.SupabaseMediaStorage':
        from django_supabase_storage.storage_backends import SupabaseMediaStorage

        folder = SupabaseMediaStorage.folder_path.strip('/')
        bucket = settings.SUPABASE_BUCKET.strip('/')
        base = settings.SUPABASE_URL.rstrip('/')
        return f'{base}/storage/v1/object/public/{bucket}/{folder}/{name.lstrip("/")}'

    if isinstance(imagen, str):
        return name
    return imagen.url
