# CodeRange Proxy Prefix and CSRF

CodeRange mounts the app at `/proxy/5001/`. `CodeRangeProxyPrefixMiddleware` normalizes the incoming WSGI script name or request path for the configured host. Keep Django URL patterns app-relative and use `{% url %}` or `redirect()` for app links. Do not manually prepend the mount in templates or set `FORCE_SCRIPT_NAME`/`DJANGO_SCRIPT_NAME`; either can duplicate the prefix.

The configured host is `itent-45-1t-2526-p23.coderange.net`; its trusted CSRF origin is `https://itent-45-1t-2526-p23.coderange.net`. Keep CSRF middleware enabled. Do not work around origin errors with wildcard trusted origins. Add new origins explicitly through `DJANGO_CSRF_TRUSTED_ORIGINS`.

If the CodeRange port or hostname changes, update the centralized `CODE_RANGE_SCRIPT_NAME`, `CODE_RANGE_HOST`, and `CODE_RANGE_ORIGIN` settings together, then test both a proxy-stripped path and a path that still contains the mount. The resulting URL must include the mount exactly once.
