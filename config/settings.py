from datetime import timedelta
from pathlib import Path
import os
from decouple import config
import pymysql
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'jobmatrix.up.railway.app', 'jobmatrixapp.netlify.app']

# Update CORS_ALLOWED_ORIGINS with your frontend URLs
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://jobmatrixapp.netlify.app"
]
# Add CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://jobmatrixapp.netlify.app'
]


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    'storages',
    "JobMatrix",
    "Profile",
    "Job"
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

# Static files settings
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# SSL/HTTPS settings
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ROOT_URLCONF = "JobMatrix.urls"
ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {"sql_mode": "STRICT_TRANS_TABLES"},
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'boto3': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        's3transfer': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

WSGI_APPLICATION = 'config.wsgi.application'

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Allow OPTIONS preflight requests to be cached for this many seconds
CORS_PREFLIGHT_MAX_AGE = 86400


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "JobMatrix.auth_backend.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

from datetime import timedelta

# JWT Configuration
JWT_SECRET= config("JWT_SECRET")
JWT_ALGORITHM= config("JWT_ALGORITHM")
JWT_EXPIRATION_DAYS= config("JWT_EXPIRATION_DAYS")

AUTH_USER_MODEL = "JobMatrix.User"

MIGRATION_MODULES = {
    "auth":None,
    "admin": None,
    "sessions": None,
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


import os
from dotenv import load_dotenv

# For production, use SMTP:
# Email settings for SendGrid
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587  # You can also use 465 for SSL
EMAIL_USE_TLS = True
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_TIMEOUT = 30
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', 'nalla4r@cmich.edu')

# AWS S3 Settings
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
print("before os ",os.environ.get('AWS_STORAGE_BUCKET_NAME'))  # Should show None if not set
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default=None)
print(f"AWS bucket name: {AWS_STORAGE_BUCKET_NAME}")  # Debug output
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default=None)

# Verify if S3 credentials are valid
USE_S3_STORAGE = False
S3_CREDENTIALS_PRESENT = all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME])

if S3_CREDENTIALS_PRESENT:
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_S3_REGION_NAME
            )

            s3.list_buckets()

            USE_S3_STORAGE = True
            
        except (ClientError, NoCredentialsError):
            pass
    except ImportError:
        pass
else:
    USE_S3_STORAGE = False

if USE_S3_STORAGE:
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_QUERYSTRING_AUTH = True  
    AWS_QUERYSTRING_EXPIRE = 604800
    AWS_LOCATION = ''
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_ADDRESSING_STYLE = 'virtual'

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default placeholder for missing images
DEFAULT_IMAGE_URL = "https://via.placeholder.com/150"