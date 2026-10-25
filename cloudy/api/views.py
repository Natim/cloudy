from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET


@require_GET
def api_root(request):
    return HttpResponseRedirect("/api/v1/docs")
