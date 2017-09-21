"""
Django settings for sambalife project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'config')
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'logs')
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'media')
PAYPAL_ROOT = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'paypal')


# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

with open(os.path.join(CONFIG_DIR, 'keys.txt')) as keys_file:
    for line in keys_file:
        key_value_pair = line.strip().split('=', 1)
        if key_value_pair[0] == 'secret_key':
            SECRET_KEY = key_value_pair[1]
        elif key_value_pair[0] == 'admin_name':
            ADMIN_NAME = key_value_pair[1]
        elif key_value_pair[0] == 'admin_email':
            ADMIN_EMAIL = key_value_pair[1]
        elif key_value_pair[0] == 'email_host':
            EMAIL_HOST = key_value_pair[1]
        elif key_value_pair[0] == 'email_port':
            EMAIL_PORT = key_value_pair[1]
        elif key_value_pair[0] == 'email_user':
            EMAIL_HOST_USER = key_value_pair[1]
        elif key_value_pair[0] == 'email_password':
            EMAIL_HOST_PASSWORD = key_value_pair[1]
        elif key_value_pair[0] == 'email_host_en':
            EMAIL_HOST_EN = key_value_pair[1]
        elif key_value_pair[0] == 'email_port_en':
            EMAIL_PORT_EN = key_value_pair[1]
        elif key_value_pair[0] == 'email_user_en':
            EMAIL_HOST_USER_EN = key_value_pair[1]
        elif key_value_pair[0] == 'email_password_en':
            EMAIL_HOST_PASSWORD_EN = key_value_pair[1]
        elif key_value_pair[0] == 'db_host':
            DB_HOST = key_value_pair[1]
        elif key_value_pair[0] == 'db_port':
            DB_PORT = key_value_pair[1]
        elif key_value_pair[0] == 'db_name':
            DB_NAME = key_value_pair[1]
        elif key_value_pair[0] == 'db_user':
            DB_USER = key_value_pair[1]
        elif key_value_pair[0] == 'db_password':
            DB_PASSWORD = key_value_pair[1]
        elif key_value_pair[0] == 'system_superuser':
            SYS_SU_USER = key_value_pair[1]
        elif key_value_pair[0] == 'system_superuser_password':
            SYS_SU_PASSWORD = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_cert_id':
            PAYPAL_CERT_ID = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_business':
            PAYPAL_BUSINESS = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_cert_id_sandbox':
            PAYPAL_CERT_ID_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_business_sandbox':
            PAYPAL_BUSINESS_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_cert_id_en':
            PAYPAL_CERT_ID_EN = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_business_en':
            PAYPAL_BUSINESS_EN = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_cert_id_en_sandbox':
            PAYPAL_CERT_ID_EN_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_business_en_sandbox':
            PAYPAL_BUSINESS_EN_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_sandbox_users':
            PAYPAL_SANDBOX_USERS = key_value_pair[1].split(',')
        elif key_value_pair[0] == 'paypal_sandbox':
            PAYPAL_SANDBOX = (key_value_pair[1] == '1')
        elif key_value_pair[0] == 'paypal_nvp_user':
            PAYPAL_NVP_USER = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_nvp_pwd':
            PAYPAL_NVP_PWD = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_nvp_signature':
            PAYPAL_NVP_SIGNATURE = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_nvp_user_sandbox':
            PAYPAL_NVP_USER_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_nvp_pwd_sandbox':
            PAYPAL_NVP_PWD_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'paypal_nvp_signature_sandbox':
            PAYPAL_NVP_SIGNATURE_SANDBOX = key_value_pair[1]
        elif key_value_pair[0] == 'django_debug':
            DJANGO_DEBUG = (key_value_pair[1] == '1')
        elif key_value_pair[0] == 'log_level':
            LOG_LEVEL = key_value_pair[1]
        elif key_value_pair[0] == 'default_redirect_factor':
            DEFAULT_REDIRECT_FACTOR = key_value_pair[1]
        elif key_value_pair[0] == 'default_amazon_fee':
            DEFAULT_AMAZON_FEE = key_value_pair[1]
        elif key_value_pair[0] == 'default_amazon_shipping_cost':
            DEFAULT_AMAZON_SHIPPING_COST = key_value_pair[1]
        elif key_value_pair[0] == 'default_fgr_cost':
            DEFAULT_FGR_COST = key_value_pair[1]
        elif key_value_pair[0] == 'default_english_version_cost':
            DEFAULT_ENGLISH_VERSION_COST = key_value_pair[1]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DJANGO_DEBUG

ALLOWED_HOSTS = ['localhost', 'vendedorinternacional.net', 'prepshiptool.com', '.maquinadevendasusa.com']
ADMINS = [(ADMIN_NAME, ADMIN_EMAIL)]

# Email configuration
EMAIL_USE_TLS = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'paypal.standard.ipn',
    'channels',
    'corsheaders',
    'statici18n',
    'utils',
    'websocket',
    'myauth',
    'product',
    'shipment',
    'payment',
    'store',
    'partner',
    'django_crontab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'utils.middleware.locale.DomainLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.terms.TermsAndConditionsMiddleware',
]

SITE_ID = 1

MIGRATION_MODULES = {
    'sites': 'fixtures.sites_migrations',
}

ROOT_URLCONF = 'sambalife.urls'

AUTH_USER_MODEL = 'myauth.MyUser'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.join(BASE_DIR, 'html'), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'sambalife.wsgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "ROUTING": "sambalife.routing.channel_routing",
        # "CONFIG": {
        #     "hosts": [("redis-channel-1", 6379), ("redis-channel-2", 6379)],
        # },
    },
}

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# https://docs.djangoproject.com/en/1.10/topics/auth/passwords/

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGES = [
    ('pt-br', _('Português')),
    ('en-us', _('Inglês')),
]

LANGUAGES_DOMAINS = {
    'vendedorinternacional.net': 'pt-br',
    'prepshiptool.com': 'en-us',
    'redirecionamento.maquinadevendasusa.com': 'pt-br',
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'html'),
]

STATIC_ROOT = os.path.join(os.path.join(BASE_DIR, 'html'), 'static')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_TRUSTED_ORIGINS = (
    'localhost',
    'vendedorinternacional.net',
    'prepshiptool.com',
    '.maquinadevendasusa.com',
)

PASSWORD_RESET_TIMEOUT_DAYS = 2

# SESSION_COOKIE_AGE = 3600

SESSION_COOKIE_SECURE = True

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'myformat': {
            'format': '%(asctime)s,%(levelname)s,%(module)s,%(threadName)s,%(processName)s ::: %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'formatter': 'myformat',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
}

PAYPAL_TEST = PAYPAL_SANDBOX

PAYPAL_PRIVATE_CERT = os.path.join(PAYPAL_ROOT, 'paypal_private.pem')
PAYPAL_PUBLIC_CERT = os.path.join(PAYPAL_ROOT, 'paypal_public.pem')
PAYPAL_PRIVATE_CERT_EN = os.path.join(PAYPAL_ROOT, 'paypal_private_en.pem')
PAYPAL_PUBLIC_CERT_EN = os.path.join(PAYPAL_ROOT, 'paypal_public_en.pem')
PAYPAL_CERT = os.path.join(PAYPAL_ROOT, 'paypal_cert.pem')
PAYPAL_CERT_SANDBOX = os.path.join(PAYPAL_ROOT, os.path.join('sandbox', 'paypal_cert.pem'))

CRONJOBS = [
    ('0 0 1 * *', 'utils.cron.archive_shipped_shipments'),
    ('0 1 * * *', 'utils.cron.price_warning'),
    # ('0   4 * * *', 'django.core.management.call_command', ['clearsessions']),
]
