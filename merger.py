"""
Merge multiple sorted log files into one unified chronological timeline.

Each log line is expected to start with an ISO 8601-ish timestamp:
    2026-11-11 09:15:12  nginx  GET /api/users  200
    2026-11-11T09:15:14  app    database connection failed

- `merge_two_streams` implements the classic two-pointer merge for
  exactly two sorted streams. O(n + m) time, O(1) extra memory.

- `merge_n_streams` generalises to any number of streams using a
  min-heap (priority queue). O(total * log k) time, O(k) extra memory,
  where k is the number of streams.

Lines whose first field isn't a parseable timestamp are skipped.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator


# Match "2026-11-11 09:15:12" OR "2026-11-11T09:15:12", with an
# optional ".fff" fractional second block.
_TIMESTAMP_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\b(.*)$"
)


@dataclass(frozen=True, order=False)
class LogEntry:
    """One line of a log file, with a parsed timestamp and the raw line."""
    time: datetime
    source: str            # which file this came from (e.g. "nginx.log")
    raw: str               # the original line, for output

    def __repr__(self) -> str:
        return f"<LogEntry {self.source} @ {self.time.isoformat()}>"


def _parse_time(text: str) -> datetime | None:
    """Try the two accepted date formats; return None if neither works."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str, source: str) -> LogEntry | None:
    """Parse one log line. Returns None if it doesn't match the format."""
    stripped = line.rstrip("\n")
    m = _TIMESTAMP_RE.match(stripped)
    if not m:
        return None
    when = _parse_time(m.group(1))
    if when is None:
        return None
    return LogEntry(time=when, source=source, raw=stripped)


def read_log_file(path: Path) -> Iterator[LogEntry]:
    """Lazy iterator over parseable lines in a log file."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            entry = parse_line(line, source=path.name)
            if entry is not None:
                yield entry


# -------------------------------------------------------------------
#                       Two-way merge (two pointers)
# -------------------------------------------------------------------

def merge_two_streams(
    a: Iterable[LogEntry],
    b: Iterable[LogEntry],
) -> Iterator[LogEntry]:
    """
    Classic two-pointer merge of two sorted streams.

    Imagine two sorted stacks of cards. At each step, look at the top
    of each stack. Take whichever is smaller. Move that pointer
    forward. Repeat. When one stack runs out, dump the rest of the
    other.
    """
    iter_a = iter(a)
    iter_b = iter(b)

    # Prime the pump: pull the first item from each stream (if any).
    cur_a = next(iter_a, None)
    cur_b = next(iter_b, None)

    while cur_a is not None and cur_b is not None:
        if cur_a.time <= cur_b.time:
            yield cur_a
            cur_a = next(iter_a, None)
        else:
            yield cur_b
            cur_b = next(iter_b, None)

    # One side is empty — drain the other.
    while cur_a is not None:
        yield cur_a
        cur_a = next(iter_a, None)
    while cur_b is not None:
        yield cur_b
        cur_b = next(iter_b, None)


# -------------------------------------------------------------------
#                    N-way merge (priority queue)
# -------------------------------------------------------------------

def merge_n_streams(streams: list[Iterable[LogEntry]]) -> Iterator[LogEntry]:
    """
    Merge N already-sorted streams into one sorted stream using a
    min-heap on timestamps.

    Keep one entry per stream in the heap. Always take the smallest
    (earliest) and refill that slot from its originating stream.

    O(total * log k) where total is total entries and k is the
    number of streams.
    """
    iters = [iter(s) for s in streams]

    # Heap entries: (time, stream_index, entry). The stream_index is
    # a tiebreaker so Python never needs to compare LogEntry objects
    # directly when timestamps are equal.
    heap: list[tuple[datetime, int, LogEntry]] = []
    for i, it in enumerate(iters):
        entry = next(it, None)
        if entry is not None:
            heapq.heappush(heap, (entry.time, i, entry))

    while heap:
        _, i, entry = heapq.heappop(heap)
        yield entry
        next_entry = next(iters[i], None)
        if next_entry is not None:
            heapq.heappush(heap, (next_entry.time, i, next_entry))


# -------------------------------------------------------------------
#                       Convenience wrapper
# -------------------------------------------------------------------

def merge_files(paths: list[Path]) -> Iterator[LogEntry]:
    """Open each file, parse, and merge. Chooses two-way or N-way."""
    streams = [read_log_file(p) for p in paths]
    if len(streams) == 2:
        return merge_two_streams(streams[0], streams[1])
    return merge_n_streams(streams)
