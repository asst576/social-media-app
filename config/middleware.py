from django.conf import settings
from django.urls import get_script_prefix, set_script_prefix


class CodeRangeProxyPrefixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        previous_prefix = get_script_prefix()
        script_name = request.META.get("SCRIPT_NAME", "").rstrip("/")
        host = request.get_host().partition(":")[0].lower()
        mount = settings.CODE_RANGE_SCRIPT_NAME

        if host == settings.CODE_RANGE_HOST and not script_name:
            script_name = mount
        while script_name.startswith(mount + mount):
            script_name = script_name[len(mount) :]

        path_info = request.path_info
        while path_info == mount or path_info.startswith(mount + "/"):
            path_info = path_info[len(mount) :] or "/"

        if script_name:
            request.META["SCRIPT_NAME"] = script_name
            set_script_prefix(script_name + "/")
        if path_info != request.path_info:
            request.path_info = path_info
            request.META["PATH_INFO"] = path_info
        request.path = f"{script_name}{path_info}"

        try:
            return self.get_response(request)
        finally:
            set_script_prefix(previous_prefix)
