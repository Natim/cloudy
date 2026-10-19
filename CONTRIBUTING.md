# Contributing

Application source is licensed under the GNU Affero General Public License v3.0 only ([LICENSE](LICENSE)). A contribution is accepted on those same terms. Third-party files keep their own licenses; see [NOTICE](NOTICE).

Please follow the [code of conduct](CODE_OF_CONDUCT.md). Report security issues privately, as described in [SECURITY.md](SECURITY.md).

## Setup

Requirements and environment variables are in [README.md](README.md).

```bash
uv sync
pre-commit install
```

`pre-commit install` runs the hooks in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) on each commit. That includes Ruff, trailing whitespace, YAML and TOML checks, and a private-key scan.

## Checks

```bash
uv run pytest
uv run ruff check cloudy/
uv run ruff format cloudy/
uv run pre-commit run --all-files
```

`uv run pytest` uses the settings in `pyproject.toml` (`DJANGO_SETTINGS_MODULE=cloudy.settings`). SQLite is enough; Postgres is optional.

`ruff check` lints. `ruff format` rewrites formatting in place. `pre-commit run --all-files` runs the full hook set, including Ruff, on the whole tree.

## What to leave alone

Do not relicense files under `cloudy/quotes/` or the vendored JavaScript listed in [NOTICE](NOTICE). New vendored JavaScript needs an entry there, with the license stated in the file.

The name Cloudy, the logos, and the artwork in `cloudy/static/img/` are not part of the AGPL grant. See [TRADEMARK.md](TRADEMARK.md).
