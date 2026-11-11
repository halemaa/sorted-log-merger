"""
Merge multiple sorted log files into one unified chronological timeline.

Usage:
    python merge.py nginx.log app.log
    python merge.py nginx.log app.log auth.log syslog.log
    python merge.py *.log                # shell expands to multiple files
    python merge.py app.log web.log --output merged.log
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from merger import merge_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge sorted log files into one chronological timeline.",
    )
    parser.add_argument(
        "logs", nargs="+",
        help="paths to sorted log files (two or more)",
    )
    parser.add_argument(
        "-o", "--output",
        help="write merged output to this file instead of stdout",
    )
    parser.add_argument(
        "--show-source", action="store_true",
        help="prefix each line with its source file name",
    )
    args = parser.parse_args()

    paths = [Path(p) for p in args.logs]
    for p in paths:
        if not p.is_file():
            print(f"Not a file: {p}", file=sys.stderr)
            return 2

    merged = merge_files(paths)

    if args.output:
        out = open(args.output, "w", encoding="utf-8")
    else:
        out = sys.stdout

    try:
        count = 0
        for entry in merged:
            if args.show_source:
                out.write(f"[{entry.source}] {entry.raw}\n")
            else:
                out.write(entry.raw + "\n")
            count += 1
        if args.output:
            print(f"Merged {count} entries from {len(paths)} files into {args.output}",
                  file=sys.stderr)
    except BrokenPipeError:
        # Downstream pipe closed (user did `| head`, etc.). Exit cleanly.
        try:
            sys.stdout.close()
        except Exception:
            pass
    finally:
        if args.output:
            out.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
