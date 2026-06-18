# Recall Monitor

Recall Monitor builds static JSON files for a recall-monitoring site. This
initial version is intentionally offline-first: it ships a sample fetcher and a
small rule classifier, but no real external data source integrations yet.

## Local install

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Run tests

```sh
pytest
```

## Offline build

```sh
python -m recall_monitor.build_data --offline-sample
```

The command writes:

- `public/data/recalls.json`
- `public/data/status.json`

## Static preview

```sh
python -m http.server 8000 --directory public
```

Open `http://localhost:8000/` to view the Chinese recall dashboard. The page
loads `./data/recalls.json` and `./data/status.json` from the generated static
files. The "我的关注关键词" field is stored only in browser `localStorage`.

Open `http://localhost:8000/data/recalls.json` or
`http://localhost:8000/data/status.json` to inspect generated data directly.

## GitHub Pages deployment

The `Update Data` workflow installs `requirements.txt`, runs:

```sh
python -m recall_monitor.build_data
```

It uploads the `public` directory to GitHub Pages. The workflow runs on a
six-hour schedule, manual `workflow_dispatch`, and pushes to `main`.

The `Test` workflow installs `requirements-dev.txt` and runs `pytest` on pushes
and pull requests.
