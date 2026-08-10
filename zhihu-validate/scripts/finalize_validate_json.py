#!/usr/bin/env python3
"""Validate and commit a Zhihu validate JSON candidate."""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn, Tuple


EXIT_JSON_ERROR = 2
EXIT_SCHEMA_ERROR = 3
EXIT_FILE_ERROR = 4
REQUIRED_FIELDS = ("type", "title", "body", "media", "linkCard", "config")
SUPPORTED_TYPES = {"article", "question", "pin"}


class SchemaError(ValueError):
    pass


def reject_nonstandard_constant(value: str) -> NoReturn:
    raise json.JSONDecodeError(f"non-standard JSON constant: {value}", value, 0)


def validate_schema(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise SchemaError("top-level value must be an object")

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise SchemaError(f"missing required field(s): {', '.join(missing)}")
    if not isinstance(payload["type"], str) or payload["type"] not in SUPPORTED_TYPES:
        raise SchemaError("type must be one of: article, question, pin")
    if not isinstance(payload["title"], str) or not isinstance(payload["body"], str):
        raise SchemaError("title and body must be strings")

    media = payload["media"]
    if not isinstance(media, (list, dict)):
        raise SchemaError("media must be an array or object")
    if isinstance(media, dict) and not isinstance(media.get("medias"), list):
        raise SchemaError("media.medias must be an array")
    if payload["linkCard"] is not None and not isinstance(payload["linkCard"], dict):
        raise SchemaError("linkCard must be an object or null")
    if not isinstance(payload["config"], dict):
        raise SchemaError("config must be an object")


def atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def commit_candidate(candidate: Path) -> Tuple[Path, Path]:
    if candidate.name != ".candidate.json":
        raise ValueError("candidate filename must be .candidate.json")

    with candidate.open("r", encoding="utf-8") as source:
        payload = json.load(source, parse_constant=reject_nonstandard_constant)
    validate_schema(payload)

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    ) + "\n"
    json.loads(serialized, parse_constant=reject_nonstandard_constant)

    output_dir = candidate.parent
    history_path = output_dir / f"{datetime.now():%Y-%m-%d-%H%M}-result.json"
    latest_path = output_dir / "latest.json"
    atomic_write(history_path, serialized)
    atomic_write(latest_path, serialized)

    try:
        candidate.unlink()
    except OSError as exc:
        print(f"warning=could not delete candidate: {exc}", file=sys.stderr)
    return history_path, latest_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and commit .candidate.json beside latest.json."
    )
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    try:
        history_path, latest_path = commit_candidate(args.candidate)
    except json.JSONDecodeError as exc:
        print(
            f"JSON parse failed at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_JSON_ERROR
    except SchemaError as exc:
        print(f"JSON schema validation failed: {exc}", file=sys.stderr)
        return EXIT_SCHEMA_ERROR
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Could not finalize validate JSON: {exc}", file=sys.stderr)
        return EXIT_FILE_ERROR

    print(f"history={history_path}")
    print(f"latest={latest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
