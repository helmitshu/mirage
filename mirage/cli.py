"""Command line interface for Mirage."""
from __future__ import annotations

import argparse
import sys
from datetime import date

from .detector import analyze
from .fetch import fetch_url
from .llm import second_opinion
from .report import render_json, render_markdown


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="mirage", description="See through ghost jobs before you apply."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Posting text")
    src.add_argument("--file", help="File containing the posting text")
    src.add_argument("--url", help="Posting URL to fetch and analyze")
    p.add_argument("--posted", help="Posting date as YYYY-MM-DD")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--no-llm", action="store_true", help="Skip the Claude second opinion")
    args = p.parse_args(argv)

    if args.text:
        text, source = args.text, "pasted text"
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        except OSError as exc:
            print(f"Could not read file: {exc}", file=sys.stderr)
            return 1
        source = args.file
    else:
        try:
            text = fetch_url(args.url)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1
        source = args.url

    posted = None
    if args.posted:
        try:
            posted = date.fromisoformat(args.posted)
        except ValueError:
            print("Bad --posted date. Use YYYY-MM-DD.", file=sys.stderr)
            return 1

    analysis = analyze(text, posted=posted)
    if not args.no_llm:
        note = second_opinion(text, analysis)
        if note:
            analysis.llm_note = note

    if args.format == "json":
        print(render_json(analysis, source=source), end="")
    else:
        print(render_markdown(analysis, source=source), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
