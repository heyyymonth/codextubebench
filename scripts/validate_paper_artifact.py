#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "docs/paper/provenance.json"
PDF = ROOT / "docs/paper/tubebench.pdf"
SCHEMA_VERSION = "tubebench.paper-artifact-provenance.v1"
REQUIRED_FIELDS = {
    "schema_version",
    "paper_revision",
    "paper_source_dirty",
    "aggregate_release_id",
    "aggregate_sha256",
    "pdf_sha256",
    "tectonic_version",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    if not PROVENANCE.is_file():
        return ["docs/paper/provenance.json is missing"]
    if not PDF.is_file():
        return ["docs/paper/tubebench.pdf is missing"]
    try:
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid paper provenance JSON: {error}"]
    if not isinstance(provenance, dict):
        return ["paper provenance root must be an object"]
    if set(provenance) != REQUIRED_FIELDS:
        errors.append("paper provenance field set is invalid")
    if provenance.get("schema_version") != SCHEMA_VERSION:
        errors.append("paper provenance schema version is invalid")
    if provenance.get("paper_source_dirty") is not False:
        errors.append("paper source must be recorded as clean")
    for field, length in (
        ("paper_revision", 40),
        ("aggregate_sha256", 64),
        ("pdf_sha256", 64),
    ):
        value = provenance.get(field)
        if not isinstance(value, str) or len(value) != length or any(
            character not in "0123456789abcdef" for character in value
        ):
            errors.append(f"paper provenance {field} is invalid")
    for field in ("aggregate_release_id", "tectonic_version"):
        if not isinstance(provenance.get(field), str) or not provenance.get(field):
            errors.append(f"paper provenance {field} is required")
    if PDF.read_bytes()[:4] != b"%PDF":
        errors.append("paper artifact does not have a PDF header")
    if provenance.get("pdf_sha256") != sha256(PDF):
        errors.append("paper PDF checksum does not match provenance")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("\n".join(errors))
        return 1
    print("paper artifact provenance passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
