from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import load_catalog, validate_catalog
from .io import read_jsonl
from .runner import run_suite, summarize_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tubebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the task catalog")
    validate.add_argument("--catalog", type=Path)

    run = subparsers.add_parser("run", help="run a deterministic mock suite")
    run.add_argument("--catalog", type=Path)
    run.add_argument(
        "--agent",
        choices=["mock-perfect", "mock-reckless", "mock-transient", "mock-noop"],
        default="mock-perfect",
    )
    run.add_argument("--seed", type=int, default=1)
    run.add_argument("--output", type=Path, required=True)

    summarize = subparsers.add_parser("summarize", help="summarize result JSONL")
    summarize.add_argument("results", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        tasks = load_catalog(args.catalog)
        errors = validate_catalog(tasks)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"valid catalog: {len(tasks)} tasks")
        return 0
    if args.command == "run":
        tasks = load_catalog(args.catalog)
        errors = validate_catalog(tasks)
        if errors:
            raise SystemExit("\n".join(errors))
        manifest = run_suite(tasks, args.agent, args.seed, args.output)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.command == "summarize":
        print(json.dumps(summarize_rows(read_jsonl(args.results)), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
