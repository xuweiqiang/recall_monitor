# Recall Monitor

Recall Monitor builds static JSON files for a recall-monitoring site. It
collects official recall data from FDA, CPSC, NHTSA, USDA FSIS, Canada Recalls,
China SAMR-style pages, EU Safety Gate, OECD GlobalRecalls, and a bundled sample
source. Sources that are blocked or temporarily unavailable are recorded in
`public/data/status.json` without stopping the whole build.

## Local install

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

## Run tests

```sh
python3 -m pytest
```

## Offline build

```sh
python3 -m recall_monitor.build_data --offline-sample
```

The command writes:

- `public/data/recalls.json`
- `public/data/status.json`

## Static preview

```sh
python3 -m http.server 8000 --directory public
```

Open `http://localhost:8000/` to view the Chinese recall dashboard. The page
loads `./data/recalls.json` and `./data/status.json` from the generated static
files. The "我的关注关键词" field is stored only in browser `localStorage`.

Open `http://localhost:8000/data/recalls.json` or
`http://localhost:8000/data/status.json` to inspect generated data directly.

## GitHub Pages deployment

The `Update Data` workflow installs `requirements.txt`, runs:

```sh
python3 -m recall_monitor.build_data
```

It uploads the `public` directory to GitHub Pages. The workflow runs on a
six-hour schedule, manual `workflow_dispatch`, and pushes to `main`.

The `Test` workflow installs `requirements-dev.txt` and runs `python -m pytest`
on pushes and pull requests.
