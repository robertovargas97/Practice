
DEBUG = True

ALLOWED_HOSTS = ["localhost"]

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'core_services_payments',
        'USER': 'user',
        'PASSWORD': 'user123',
        'HOST': '127.0.0.1',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
            'charset': 'utf8mb4'
        },
        'TIME_ZONE': 'America/New_York',
        'TEST': {
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
            }
    }
}
