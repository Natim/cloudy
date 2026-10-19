import json

from django.http import HttpResponse


def json_ok(data={}):
    return HttpResponse(json.dumps({"success": True, "data": data}), content_type="application/json")


def json_fail(msg):
    return HttpResponse(json.dumps({"success": False, "msg": msg}), content_type="application/json")
