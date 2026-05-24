"""Command-line entry point for the If-PBM open demo."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from importlib import resources
from pathlib import Path

from .pipeline import DEFAULT_DB_PATH, build, compute, generate_database


def _launch_dashboard(db_path: Path) -> int:
    env = dict(os.environ, IF_PBM_DB=str(db_path))
    dashboard = resources.files(__package__).joinpath("dashboard.py")
    with resources.as_file(dashboard) as path:
        return subprocess.call(
            [sys.executable, "-m", "streamlit", "run", str(path)], env=env
        )


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch a subcommand.

    Subcommands: ``generate`` (canonical data), ``indicators`` (compute the mart),
    ``dashboard`` (launch Streamlit), ``demo`` (all of the above).
    """
    parser = argparse.ArgumentParser(prog="if-pbm-demo", description=__doc__)
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH, help="DuckDB file path"
    )
    parser.add_argument("--seed", type=int, default=42, help="Generator seed")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate", help="Generate synthetic canonical data")
    sub.add_parser("indicators", help="Compute the indicator results mart")
    sub.add_parser("dashboard", help="Launch the Streamlit dashboard")
    sub.add_parser("demo", help="Generate, compute, then launch the dashboard")

    args = parser.parse_args(argv)

    if args.command == "generate":
        path = generate_database(args.db, args.seed)
        print(f"Generated canonical data -> {path}")
        return 0
    if args.command == "indicators":
        compute(args.db)
        print(f"Computed indicator_results mart -> {args.db}")
        return 0
    if args.command == "dashboard":
        return _launch_dashboard(args.db)
    if args.command == "demo":
        build(args.db, args.seed)
        print(f"Built {args.db}; launching dashboard...")
        return _launch_dashboard(args.db)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
