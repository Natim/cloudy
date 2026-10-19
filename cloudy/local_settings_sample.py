# Copy to cloudy/local_settings.py and adjust for your machine (optional overrides).

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "localhost:8000"]

INTERNAL_IPS = ["127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "localhost",
        "NAME": "cloudy_dj4",
        "USER": "cloudy",
        "PASSWORD": "cloudypwd",
        "PORT": "5432",
    }
}

REDIS_SERVER = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1
REDIS_PASSWORD = None

CONSTANCE_REDIS_CONNECTION = {
    "host": REDIS_SERVER,
    "port": REDIS_PORT,
    "db": REDIS_DB,
}
if REDIS_PASSWORD:
    CONSTANCE_REDIS_CONNECTION["password"] = REDIS_PASSWORD

CACHING = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_SERVER}:{REDIS_PORT}/{REDIS_DB}",
    }
}
