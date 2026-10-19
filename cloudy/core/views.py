from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

# Create your views here.


def home(request, template="home.html"):
    """
    Home page
    """
    if not request.user.is_anonymous:
        return HttpResponseRedirect(reverse("logbooks:home"))

    # resp = render(template, {}, RequestContext(request))
    return render(request, template)

    # # do we need to set a cookie when sponsoring params are present ?  # DELETE
    # # Look for p & uid in get vars
    # if "p" in request.GET and "uid" in request.GET:
    #     resp.set_cookie("sponso_p", value=request.GET["p"])
    #     resp.set_cookie("sponso_uid", value=request.GET["uid"])
    # return resp
