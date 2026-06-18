# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import codecs
import os

from recall_monitor.classifier import classify_record_text
from recall_monitor.fetchers.base import utc_now_iso
from recall_monitor.fetchers.base import sanitize_url
from recall_monitor.fetchers.canada import CanadaFetcher
from recall_monitor.fetchers.china import ChinaFetcher
from recall_monitor.fetchers.cpsc import CpscFetcher
from recall_monitor.fetchers.eu import EuSafetyGateFetcher
from recall_monitor.fetchers.fda import FdaFetcher
from recall_monitor.fetchers.nhtsa import NhtsaFetcher
from recall_monitor.fetchers.oecd import OecdFetcher
from recall_monitor.fetchers.sample import SampleFetcher
from recall_monitor.fetchers.usda import UsdaFetcher
from recall_monitor.model import SourceStatus, dumps_json


DEFAULT_OUTPUT_DIR = os.path.join("public", "data")


def default_fetchers(offline_sample=False):
    if offline_sample:
        return [SampleFetcher()]
    return [
        FdaFetcher("food"),
        FdaFetcher("drug"),
        FdaFetcher("device"),
        CpscFetcher(),
        NhtsaFetcher(),
        UsdaFetcher(),
        CanadaFetcher(),
        ChinaFetcher(),
        EuSafetyGateFetcher(),
        OecdFetcher(),
        SampleFetcher(),
    ]


def build_data(fetchers, output_dir=DEFAULT_OUTPUT_DIR):
    _mkdirs(output_dir)

    records = []
    statuses = []

    for fetcher in fetchers:
        fetched_at = utc_now_iso()
        source = getattr(fetcher, "name", fetcher.__class__.__name__)
        try:
            result = fetcher.fetch()
        except Exception as exc:  # Keep one source failure from blocking the build.
            statuses.append(
                SourceStatus(
                    source=source,
                    ok=False,
                    fetched_at=fetched_at,
                    count=0,
                    error=str(exc),
                )
            )
            continue

        source_records = [_classified_record(record) for record in result.records]
        records.extend(source_records)
        status = getattr(result, "status", None)
        if status is None:
            status = SourceStatus(
                source=result.source,
                ok=True,
                fetched_at=fetched_at,
                count=len(source_records),
            )
        statuses.append(status)

    records.sort(key=lambda record: (record.published_at, record.id), reverse=True)

    recalls_path = _join_path(output_dir, "recalls.json")
    status_path = _join_path(output_dir, "status.json")
    generated_at = utc_now_iso()
    _write_text(
        recalls_path,
        dumps_json(
            {
                "generated_at": generated_at,
                "records": [record.to_public_dict() for record in records],
            }
        ),
    )
    _write_text(
        status_path,
        dumps_json(
            {
                "generated_at": generated_at,
                "sources": [status.to_dict() for status in statuses],
            }
        ),
    )

    return {
        "recalls_path": recalls_path,
        "status_path": status_path,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Recall Monitor static data.")
    parser.add_argument(
        "--offline-sample",
        action="store_true",
        help="Build only with bundled sample data.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated JSON files.",
    )
    args = parser.parse_args(argv)

    fetchers = default_fetchers(offline_sample=args.offline_sample)
    build_data(fetchers, args.output_dir)
    return 0


def _classified_record(record):
    record.source_url = sanitize_url(record.source_url)
    text = " ".join([record.title_original, record.title_zh, record.summary_zh])
    classification = classify_record_text(text)

    if not record.categories:
        record.categories = list(classification["categories"])
    if not record.risks:
        record.risks = list(classification["risks"])
    if record.severity == "unknown":
        record.severity = classification["severity"]
    if not record.action:
        record.action = classification["action"]
    if not record.dedupe_key:
        record.dedupe_key = stable_record_key(record)
    return record


def stable_record_key(record):
    from recall_monitor.fetchers.base import stable_id

    return stable_id(record.brand, record.product, record.model, ",".join(record.risks))


def _join_path(output_dir, filename):
    try:
        return output_dir / filename
    except TypeError:
        return os.path.join(output_dir, filename)


def _mkdirs(output_dir):
    if hasattr(output_dir, "mkdir"):
        output_dir.mkdir(parents=True, exist_ok=True)
        return
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)


def _write_text(path, text):
    if hasattr(path, "write_text"):
        path.write_text(text, encoding="utf-8")
        return
    with codecs.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


if __name__ == "__main__":
    raise SystemExit(main())
