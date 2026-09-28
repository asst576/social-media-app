# Development and Operations

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:5001
```

Open the CodeRange preview on port `5001`. SQLite data is stored in `db.sqlite3`; local uploads are stored in `media/`. Both are Git-ignored.

Development settings default to `DJANGO_DEBUG=1`. If `DJANGO_SECRET_KEY` is omitted in debug mode, a temporary process key is generated and sessions will be invalidated after restart. Non-debug mode requires `DJANGO_SECRET_KEY`. `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` add comma-separated entries to the configured localhost and CodeRange values.

## CodeRange Proxy

The CodeRange preview mounts the app at `/proxy/5001/`. `CodeRangeProxyPrefixMiddleware` normalizes the WSGI script name or request path for the configured CodeRange host. Root URL patterns remain app-relative, and templates use Django URL reversing for application links and form actions.

Do not set `FORCE_SCRIPT_NAME` or `DJANGO_SCRIPT_NAME`; forcing the mount when the proxy already supplies it can duplicate `/proxy/5001/`. See [CodeRange proxy and CSRF](footguns/coderange-proxy.md).

The configured trusted CSRF origin is `https://itent-45-1t-2526-p23.coderange.net`. CSRF protection remains enabled. Add any additional deployment origin explicitly, including its scheme.

## Campaign Manager and Staff Setup

Create a staff superuser with `python manage.py createsuperuser`, then sign in at `/admin/`. Edit a user and assign the **Campaign manager** role. Do not set `is_staff` on campaign managers unless they also require admin access.

Managers create drafts and submit them for review. After staff approval, the manager can simulate a purchase. Staff can approve/reject pending campaigns and pause/resume approved campaigns.

## Validation

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

Before public deployment, disable debug mode, supply a stable secret, set deployment-specific hosts and CSRF origins, and configure persistent media storage/serving. The current SQLite and local media setup is for development.
