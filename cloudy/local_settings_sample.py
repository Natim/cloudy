ALLOWED_HOSTS = ["localhost:8000", "127.0.0.1"]
INTERNAL_IPS = [
    "127.0.0.1",
]

DATABASES = {
    "default": {
        "HOST": "localhost",
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "cloudy_dj4",
        "USER": "cloudy",
        "PASSWORD": "cloudypwd",
    }
}

# REDIS_PASSWORD = None
# INTERNAL_IPS = ("0.0.0.0", "127.0.0.1", "10.0.100.90")
# # TEST
# STRIPE_API_KEY = ""
# STRIPE_FIRST_CLASS_SUBSCRIPTION = ""


# EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
# EMAIL_FILE_PATH = "/home/www/logs/mail"

# CACHING = True
# LOGS_FOR_REAL = False


# TEST_RUNNER = "django.test.simple.DjangoTestSuiteRunner"
REDIS_SERVER = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1
REDIS_PASSWORD = None

CONSTANCE_CONNECTION = {
    "host": REDIS_SERVER,
    "port": REDIS_PORT,
    "db": REDIS_DB,
    "password": REDIS_PASSWORD,
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://%s:%s" % (REDIS_SERVER, REDIS_PORT),
        "OPTIONS": {
            "db": REDIS_DB,
            "password": REDIS_PASSWORD,
            "parser_class": "redis.connection.HiredisParser",
            "pool_class": "redis.BlockingConnectionPool",
        },
    },
}
