from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-local-development-only',
)

ALLOWED_HOSTS = ['*']

LOGIN_URL = 'login_cliente'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'productos',
    'contact',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'productos.context_processors.cart_processor',
            ],
        },
    },
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400

WSGI_APPLICATION = 'ecommerce.wsgi.application'

try:
    import dj_database_url
    database_url = os.environ.get('DATABASE_URL', '')
    is_postgres = database_url.startswith('postgres://') or database_url.startswith('postgresql://')
    DATABASES = {
        'default': dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            ssl_require=not DEBUG if is_postgres else False,
        )
    }
except ImportError as exc:
    if os.environ.get('DATABASE_URL'):
        raise ImproperlyConfigured(
            'Install dj-database-url to use DATABASE_URL.'
        ) from exc
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-AR'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de Almacenamiento (Django 5.x)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Supabase Storage
SUPABASE_PROJECT_ID = os.environ.get('SUPABASE_PROJECT_ID', '').strip()
SUPABASE_URL = os.environ.get('SUPABASE_URL') or (
    f'https://{SUPABASE_PROJECT_ID}.supabase.co'
    if SUPABASE_PROJECT_ID else ''
)
SUPABASE_KEY = (
    os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    or os.environ.get('SUPABASE_KEY')
)
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'productos')

if bool(SUPABASE_URL) != bool(SUPABASE_KEY):
    raise ImproperlyConfigured(
        'Configure SUPABASE_URL (or SUPABASE_PROJECT_ID) and '
        'SUPABASE_SERVICE_ROLE_KEY together.'
    )

if SUPABASE_URL and SUPABASE_KEY:
    STORAGES["default"] = {
        "BACKEND": "django_supabase_storage.SupabaseMediaStorage",
    }
    SUPABASE_PUBLIC_URL = True 


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = os.environ.get('MERCADO_PAGO_PUBLIC_KEY', '')
MERCADO_PAGO_ACCESS_TOKEN = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN', '')

# Wavespeed AI
WAVESPEED_API_TOKEN = os.environ.get('WAVESPEED_API_TOKEN', '')

# Upload Limits para VTON (20 MB en el servidor, validamos 15 MB en el código)
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520   # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520   # 20 MB

# ========== CONFIGURACIÓN DE EMAIL ==========
_email_user = os.environ.get('EMAIL_HOST_USER', '')
_email_pass = os.environ.get('EMAIL_HOST_PASSWORD', '')

if DEBUG and not (_email_user and _email_pass):
    # En desarrollo: muestra el email en la consola del servidor (no envía nada real)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # En producción: envía via Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = _email_user
    EMAIL_HOST_PASSWORD = _email_pass
    DEFAULT_FROM_EMAIL = _email_user

# Token de reset de contraseña expira en 1 hora
PASSWORD_RESET_TIMEOUT = 3600