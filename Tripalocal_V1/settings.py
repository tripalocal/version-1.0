"""
Django settings for Tripalocal_V1 project.
"""
import os

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from os import path, environ
PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))

from django.utils.translation import ugettext_lazy as _

DEBUG = True #False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['tripalocal.com','www.tripalocal.com']

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tripalocal_v1',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    },
    'maildb': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'maildb',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}

DATABASE_ROUTERS = ['tripalocal_messages.routers.message_router']

DATABASE_APPS_MAPPING = {'tripalocal_messages':'maildb'}

LOGIN_URL = '/accounts/login'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Australia/Melbourne'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-au'

LANGUAGES = (
    ('en', _('English')),
    ('zh', _('Chinese')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = path.join(PROJECT_ROOT, 'images').replace('\\', '/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/images/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path.join(PROJECT_ROOT, 'static').replace('\\', '/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path.join(PROJECT_ROOT, 'app/static/'),
    path.join(PROJECT_ROOT, 'experiences/static/'),
    path.join(PROJECT_ROOT, 'custom_admin/static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n(bd1f1c%e8=_xad02x5qtfn%wgwpi492e$8_erx+d)!tpeoim'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'Tripalocal_V1.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'Tripalocal_V1.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path.join(PROJECT_ROOT, 'templates'),
    path.join(PROJECT_ROOT, 'app/templates'),
    path.join(PROJECT_ROOT, 'experiences/templates'),
    path.join(PROJECT_ROOT, 'custom_admin/templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'bootstrap3_datetime',
    'app',
    'experiences',
    'tripalocal_messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    #"sendgrid",
    "payments",
    "mathfilters",
    "formwizard",
    'post_office',
    'rest_framework',
    'rest_framework.authtoken',
    #'storages',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(module)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': path.join(PROJECT_ROOT, 'tripalocal.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'Tripalocal_V1': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

# Specify the default test runner.
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

AUTH_PROFILE_MODULE = "experience.RegisteredUser"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
    "app.views.current_datetime",
    "django.contrib.messages.context_processors.messages",
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend"
)

SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'SCOPE': ['email'],
        'METHOD': 'js_sdk'  # instead of 'oauth2'
    }
}
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_ADAPTER = 'app.allauth.AccountAdapter'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/registration_successful'
ACCOUNT_SIGNUP_FORM_CLASS = 'app.forms.SignupForm'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_VERIFICATION = False

#SENDGRID_EMAIL_HOST = "smtp.sendgrid.net"
#SENDGRID_EMAIL_PORT = 587
#SENDGRID_EMAIL_USER = ""
#SENDGRID_EMAIL_PASSWORD = ""
#EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Tripalocal <enquiries@tripalocal.com>' #Default email address to use for various automated correspondence from the site manager
SERVER_EMAIL = 'Tripalocal <enquiries@tripalocal.com>' #The email address that error messages come from
EMAIL_HOST = ''#The host to use for sending email
EMAIL_PORT = 25
EMAIL_HOST_USER = ''#only used for authentication on the mail server
EMAIL_HOST_PASSWORD = ''
EMAIL_BACKEND = 'post_office.EmailBackend' #'django.core.mail.backends.smtp.EmailBackend'#'django.core.mail.backends.console.EmailBackend'#

STRIPE_SECRET_KEY = environ.get(
    "STRIPE_SECRET_KEY",
    "sk_test_"
)
STRIPE_PUBLIC_KEY = environ.get(
    "STRIPE_PUBLIC_KEY",
    "pk_test_"
)

STRIPE_PRICE_PERCENT = 0.000 #0.029
STRIPE_PRICE_FIXED = 0.00 #0.30
COMMISSION_PERCENT = 0.429

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

DOMAIN_NAME = 'tripalocal.com'

#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True

MIXPANEL_TOKEN = ''

SESSION_COOKIE_NAME = 'Tripalocal_sessionid'

POST_OFFICE = {
    'DEFAULT_PRIORITY': 'now'
}

GEO_POSTFIX = "/"

DEVELOPMENT = False

# AWS S3
AWS_STORAGE_BUCKET_NAME = 'tripalocal-static'
AWS_ACCESS_KEY_ID = 'AKIAJ2SSSHLAOMYAKHCQ'
AWS_SECRET_ACCESS_KEY = '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'

AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

STATICFILES_LOCATION = 'static'
MEDIAFILES_LOCATION = 'images'


if 'DEFAULT_FILE_STORAGE' in os.environ:
    DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE')
    MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)

if 'STATICFILES_STORAGE' in os.environ:
    STATICFILES_STORAGE = os.environ.get('STATICFILES_STORAGE')
    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)


# Customized settings should always be put at the bottom
if os.environ.get('ENV_MODE') == 'DEVELOPMENT':
    try:
        from test_settings import *
    except ImportError:
        pass

try:
    from local_settings import *
except ImportError:
    pass