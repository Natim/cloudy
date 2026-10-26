# Cloudy

Online pilot logbooks ([cloudy.fr](https://www.cloudy.fr/)).

## API

[elm-cloudy](https://github.com/Natim/elm-cloudy) is an example client for `/api/v1`: an Elm HTTP package and an [offline-first PWA](https://natim.github.io/elm-cloudy/).

## License

Application source code is released under the **GNU Affero General Public License v3.0 only** ([LICENSE](LICENSE)). Copyright SAS CLOUDY.

If you run a modified version so that users interact with it over a network, the AGPL requires you to offer those users the corresponding source of your version.

The AGPL does not cover:

- the name **Cloudy**, the logos, and the graphic identity ([TRADEMARK.md](TRADEMARK.md))
- illustrations, photographs, and site artwork in `cloudy/static/img/`
- fonts in `cloudy/static/fonts/` and `cloudy/static/pdf/`

Third-party files keep their own terms. `cloudy/quotes/` is BSD code by Randall Degges. Vendored JavaScript under `cloudy/static/js/` keeps the license stated for each file. See [NOTICE](NOTICE).

The production branch runs Django **6.1.2** on Python **3.14**, upgraded from the
legacy Django 1.4 / Python 2 stack.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- Python 3.14 (see `.python-version`)
- PostgreSQL 15+ (optional; SQLite is enough for local development)
- Redis (django-constance; optional logbook pagination cache)

## Setup

```bash
uv sync
cp .env.example .env   # then edit secrets
pre-commit install
```

Settings are read from the environment (`cloudy/settings.py`). The project does
not load `.env` automatically, so export the variables before `runserver`:

```bash
set -a && source .env && set +a
```

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret (required when `DJANGO_DEBUG` is not `true`) |
| `DJANGO_DEBUG` | Defaults to `false`; set `true` for local dev (see `.env.example`) |
| `DATABASE_URL` | If it starts with `postgres`, Postgres is used; otherwise SQLite `db.sqlite3` |
| `POSTGRES_*` | Name / user / password / host / port when using Postgres |
| `STRIPE_API_KEY`, `STRIPE_FIRST_CLASS_SUBSCRIPTION`, `STRIPE_WEBHOOK_SECRET` | Billing |
| `GOOGLE_ANALYTICS_PROPERTY_ID` | Optional `UA-…` property; leave empty to disable |
| `GAUGES_SITE_ID` | Optional Gauges site id; leave empty to disable |
| `EMAIL_HOST` | SMTP host; if unset, emails are printed to the console |
| `IMPORT_DEFAULT_OWNER_EMAIL` | Staff user who receives manual logbook uploads |

## Run

SQLite (empty local DB):

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

## Tests and lint

```bash
uv run pytest
uv run ruff check cloudy/ && uv run ruff format cloudy/
uv run pre-commit run --all-files
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Deploy

`deploy.sh` runs `uv sync`, `collectstatic`, compressor, and a gunicorn HUP.
WSGI entrypoint: `cloudy.wsgi:application`.
