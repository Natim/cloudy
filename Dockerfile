# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev
# Four files referenced by the CSS/JS are missing from the repository and make collectstatic
# fail: reuse the existing spinner image and add empty source maps, only when they are absent.
RUN cd cloudy/static \
 && { [ -e compass/stylesheets/loading.gif ] || cp img/ajax-loader.gif compass/stylesheets/loading.gif; } \
 && { [ -e img/spinner.gif ] || cp img/ajax-loader.gif img/spinner.gif; } \
 && { [ -e js/chartjs/chart.umd.js.map ] || touch js/chartjs/chart.umd.js.map; } \
 && { [ -e js/leaflet/leaflet.js.map ] || touch js/leaflet/leaflet.js.map; }
# Static files and compressed bundles are built into the image, as deploy.sh does on the server.
RUN DJANGO_SECRET_KEY=build-only-placeholder-not-used-at-runtime DJANGO_DEBUG=false \
    .venv/bin/python manage.py collectstatic --noinput \
 && DJANGO_SECRET_KEY=build-only-placeholder-not-used-at-runtime DJANGO_DEBUG=false \
    .venv/bin/python manage.py compress --force


FROM python:3.14-slim-bookworm
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cloudy.settings
RUN groupadd --system cloudy && useradd --system --gid cloudy --home-dir /app cloudy
WORKDIR /app
COPY --from=build --chown=cloudy:cloudy /app /app
RUN mkdir -p /app/media && chown cloudy:cloudy /app /app/media
USER cloudy
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/v1/openapi.json', headers={'X-Forwarded-Proto': 'https'}), timeout=4)"]
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "cloudy.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--forwarded-allow-ips", "*", "--access-logfile", "-"]
