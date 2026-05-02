from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-%h!a1lf_h0a05(#=(_aabbq0a*z+s&c1=a^9zualpba%f424is'

DEBUG = True

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
    DATABASES = {
        'default': dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600
        )
    }
except ImportError:
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

# Supabase Storage (Nube)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'productos')

if SUPABASE_URL and SUPABASE_KEY:
    STORAGES["default"] = {
        "BACKEND": "django_supabase_storage.SupabaseStorage",
    }
    SUPABASE_PUBLIC_URL = True 


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = "APP_USR-94cc2d5d-82e5-44da-8612-afee97d487fb"
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-7762497834204355-042410-ec020e65e4436130b4f6a98387a60ee3-1109104702"

# Wavespeed AI
WAVESPEED_API_TOKEN = "953d8203e32cf8dfa905e5e848793beba21295defdf928876d07efe86199f050"

# Upload Limits para VTON (20 MB en el servidor, validamos 15 MB en el código)
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520   # 20 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520   # 20 MB

# ========== CONFIGURACIÓN DE EMAIL ==========
_email_user = os.environ.get('EMAIL_HOST_USER', 'carlomagnocordoba@gmail.com')
_email_pass = os.environ.get('EMAIL_HOST_PASSWORD', 'yjco aysa fdhu fskd')

if DEBUG and not _email_user:
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