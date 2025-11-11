"""
Django settings for DjangoProject project.
"""

from pathlib import Path
import os
import dj_database_url  # Para conexión con Railway

# --- Directorios base ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad ---
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-cqfaca4z*=)rx+b97o%^2lco$n@^o9&o2p_9g+yuqtkz5w)e$u')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    "perfectteeth-production.up.railway.app",
    "127.0.0.1",
    "localhost"
]

CSRF_TRUSTED_ORIGINS = [
    "https://perfectteeth-production.up.railway.app"
]

# --- Aplicaciones ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'usuarios',  # Tu app
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # necesario para CSS/JS en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DjangoProject.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject.wsgi.application'


# --- Base de datos ---
# Por defecto usa SQLite (para desarrollo local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Si Railway define DATABASE_URL, se usa PostgreSQL remoto automáticamente
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )


# --- Validadores de contraseña ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Configuración regional ---
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # carpeta donde está tu CSS, JS e imágenes
STATIC_ROOT = BASE_DIR / "staticfiles"    # carpeta de compilación para producción

# WhiteNoise optimización
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- Campo automático por defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
