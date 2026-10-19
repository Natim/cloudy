from django.http import HttpResponseRedirect
from django.urls import reverse

REDIRECTS = ({"user_agent": ("msie 7", "msie 6"), "redirect_to": "ie6"},)


class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        redirect = self._maybe_redirect(request)
        if redirect is not None:
            return redirect
        return self.get_response(request)

    def _maybe_redirect(self, request):
        request_ua = request.META.get("HTTP_USER_AGENT", "").lower()

        for redirect in REDIRECTS:
            user_agents = redirect["user_agent"]

            not_c = redirect.get("not_contains")
            if not_c is not None and not_c in request.path:
                return None

            if isinstance(user_agents, str):
                user_agents = (user_agents,)
            for uagent in user_agents:
                if uagent in request_ua:
                    cookies = redirect.get("cookie")
                    if cookies is not None:
                        if isinstance(cookies, str):
                            cookies = (cookies,)

                        all_out = True
                        for cookie in cookies:
                            if request.COOKIES.get(cookie) is not None:
                                all_out = False
                                break

                        if all_out:
                            url = reverse(redirect["redirect_to"])
                            if url not in request.path:
                                return HttpResponseRedirect(url)
        return None
