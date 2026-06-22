from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import load_catalog, validate_catalog
from .executable import (
    load_executable_catalog,
    run_executable_suite,
    score_trace_file,
    validate_executable_catalog,
)
from .fixture_server import serve
from .io import read_jsonl
from .live_youtube import (
    load_live_youtube_catalog,
    validate_live_youtube_catalog,
    validate_live_youtube_trace,
)
from .io import read_json
from .longform_catalog import load_longform_catalog, validate_longform_catalog
from .runner import run_suite, summarize_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tubebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the task catalog")
    validate.add_argument("--catalog", type=Path)

    validate_longform = subparsers.add_parser(
        "validate-longform",
        help="validate the long-form seed task catalog",
    )
    validate_longform.add_argument("--catalog", type=Path)

    validate_executable = subparsers.add_parser(
        "validate-executable",
        help="validate TubeControl-Executable-v0",
    )
    validate_executable.add_argument("--catalog", type=Path)

    validate_live = subparsers.add_parser(
        "validate-live-youtube",
        help="validate the experimental live_youtube_v0 catalog",
    )
    validate_live.add_argument("--catalog", type=Path)

    validate_live_trace = subparsers.add_parser(
        "validate-live-youtube-trace",
        help="validate one private live YouTube trace",
    )
    validate_live_trace.add_argument("trace", type=Path)

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

    run_executable = subparsers.add_parser(
        "run-executable",
        help="run deterministic executable baselines and emit trace artifacts",
    )
    run_executable.add_argument("--catalog", type=Path)
    run_executable.add_argument(
        "--agent",
        choices=["scripted", "noop", "random", "transcript-only"],
        default="scripted",
    )
    run_executable.add_argument("--seed", type=int, default=1)
    run_executable.add_argument("--task", action="append", dest="tasks")
    run_executable.add_argument(
        "--mode",
        choices=["gui_native", "ui_assisted", "instrumented_browser", "hybrid"],
    )
    run_executable.add_argument("--output", type=Path, required=True)

    score_trace = subparsers.add_parser(
        "score-executable-trace",
        help="replay and score one executable trace",
    )
    score_trace.add_argument("trace", type=Path)
    score_trace.add_argument("--catalog", type=Path)
    score_trace.add_argument("--output", type=Path)

    fixture = subparsers.add_parser(
        "serve-fixture",
        help="serve the deterministic local long-form player",
    )
    fixture.add_argument("--host", default="127.0.0.1")
    fixture.add_argument("--port", type=int, default=8765)
    fixture.add_argument("--catalog", type=Path)
    fixture.add_argument("--oracle-token")
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
    if args.command == "validate-longform":
        tasks = load_longform_catalog(args.catalog)
        errors = validate_longform_catalog(tasks)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"valid long-form catalog: {len(tasks)} tasks")
        return 0
    if args.command == "validate-executable":
        tasks = load_executable_catalog(args.catalog)
        errors = validate_executable_catalog(tasks)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"valid executable catalog: {len(tasks)} tasks")
        return 0
    if args.command == "validate-live-youtube":
        tasks = load_live_youtube_catalog(args.catalog)
        errors = validate_live_youtube_catalog(tasks)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"valid live YouTube catalog: {len(tasks)} tasks")
        return 0
    if args.command == "validate-live-youtube-trace":
        trace = read_json(args.trace)
        if not isinstance(trace, dict):
            print("live YouTube trace root must be an object")
            return 1
        errors = validate_live_youtube_trace(trace)
        if errors:
            print("\n".join(errors))
            return 1
        print(f"valid live YouTube trace: {trace['task_id']}")
        return 0
    if args.command == "run-executable":
        tasks = load_executable_catalog(args.catalog)
        errors = validate_executable_catalog(tasks)
        if errors:
            raise SystemExit("\n".join(errors))
        manifest = run_executable_suite(
            tasks,
            agent=args.agent,
            seed=args.seed,
            output=args.output,
            task_ids=args.tasks,
            mode=args.mode,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.command == "score-executable-trace":
        result = score_trace_file(
            args.trace,
            output_path=args.output,
            catalog_path=args.catalog,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "serve-fixture":
        serve(
            host=args.host,
            port=args.port,
            catalog_path=args.catalog,
            oracle_token=args.oracle_token,
        )
        return 0
    if args.command == "summarize":
        print(json.dumps(summarize_rows(read_jsonl(args.results)), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
