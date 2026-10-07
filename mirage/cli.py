"""Command line interface for Mirage."""
from __future__ import annotations

import argparse
import sys
from datetime import date

from . import __version__
from .detector import analyze
from .fetch import fetch_url
from .llm import second_opinion
from .report import render_json, render_markdown
from .translator import translate


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="mirage", description="See through ghost jobs before you apply."
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Posting text")
    src.add_argument("--file", help="File containing the posting text")
    src.add_argument("--url", help="Posting URL to fetch and analyze")
    p.add_argument("--posted", help="Posting date as YYYY-MM-DD")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--no-llm", action="store_true", help="Skip the Claude second opinion")
    p.add_argument(
        "--translate",
        action="store_true",
        help="Add the plain English translation of the posting",
    )
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
    translation = translate(text) if args.translate else None

    if args.format == "json":
        print(render_json(analysis, source=source, translation=translation), end="")
    else:
        print(
            render_markdown(analysis, source=source, translation=translation), end=""
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
