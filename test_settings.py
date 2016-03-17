# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASES = {}
DATABASES['default'] =  dj_database_url.config(default='mysql://username:password@server:port/tripalocal_v1')
DATABASES['maildb'] =  dj_database_url.config(default='mysql://username:password@server:port/maildb')
MIXPANEL_TOKEN = 'c2510512c6cb4c34b4b32bd32a0cf866'
DEVELOPMENT = True