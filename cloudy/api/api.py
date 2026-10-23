from ninja import NinjaAPI

from .openapi_schemas import enrich_openapi_schema
from .routes import router

api = NinjaAPI(
    title="Cloudy Logbook API",
    version="1.0.0",
    description="Mobile logbook read/write API for cloudy.fr pilots.",
    urls_namespace="cloudy_api",
)

api.add_router("", router)

_original_get_openapi_schema = api.get_openapi_schema


def _get_openapi_schema(*args, **kwargs):
    return enrich_openapi_schema(_original_get_openapi_schema(*args, **kwargs))


api.get_openapi_schema = _get_openapi_schema
