"""Tests for the log merger."""

from datetime import datetime
from pathlib import Path

import pytest

from merger import (
    LogEntry,
    merge_n_streams,
    merge_two_streams,
    parse_line,
)


def _entry(ts: str, source: str = "test", raw: str | None = None) -> LogEntry:
    """Convenience: build a LogEntry from an ISO-ish timestamp."""
    when = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    return LogEntry(time=when, source=source, raw=raw or f"{ts} {source}")


# ---------- parsing ----------

def test_parse_valid_iso_line():
    entry = parse_line("2026-11-11 09:15:12  nginx  GET /api/users 200", "nginx.log")
    assert entry is not None
    assert entry.time == datetime(2026, 11, 11, 9, 15, 12)
    assert entry.source == "nginx.log"


def test_parse_valid_t_format():
    entry = parse_line("2026-11-11T09:15:12 app message", "app.log")
    assert entry is not None
    assert entry.time == datetime(2026, 11, 11, 9, 15, 12)


def test_parse_rejects_non_log_line():
    assert parse_line("random text with no timestamp", "x") is None
    assert parse_line("", "x") is None
    assert parse_line("# a comment", "x") is None


# ---------- two-way merge ----------

def test_merge_two_empty_streams():
    assert list(merge_two_streams([], [])) == []


def test_merge_two_one_empty():
    a = [_entry("2026-01-01 10:00:00")]
    assert list(merge_two_streams(a, [])) == a
    assert list(merge_two_streams([], a)) == a


def test_merge_two_perfect_interleave():
    a = [_entry("2026-01-01 10:00:01"), _entry("2026-01-01 10:00:03")]
    b = [_entry("2026-01-01 10:00:02"), _entry("2026-01-01 10:00:04")]
    result = list(merge_two_streams(a, b))
    times = [e.time for e in result]
    assert times == sorted(times)
    assert len(result) == 4


def test_merge_two_all_a_before_b():
    a = [_entry("2026-01-01 10:00:00"), _entry("2026-01-01 10:00:01")]
    b = [_entry("2026-01-01 11:00:00"), _entry("2026-01-01 11:00:01")]
    result = list(merge_two_streams(a, b))
    assert result == a + b


def test_merge_two_duplicate_timestamps_stable():
    """When timestamps tie, stream A's entries should come first."""
    a = [_entry("2026-01-01 10:00:00", source="a")]
    b = [_entry("2026-01-01 10:00:00", source="b")]
    result = list(merge_two_streams(a, b))
    assert result[0].source == "a"
    assert result[1].source == "b"


# ---------- N-way merge ----------

def test_merge_n_three_streams():
    a = [_entry("2026-01-01 10:00:01"), _entry("2026-01-01 10:00:04")]
    b = [_entry("2026-01-01 10:00:02"), _entry("2026-01-01 10:00:05")]
    c = [_entry("2026-01-01 10:00:03"), _entry("2026-01-01 10:00:06")]
    result = list(merge_n_streams([a, b, c]))
    times = [e.time for e in result]
    assert times == sorted(times)
    assert len(result) == 6


def test_merge_n_handles_empty_streams():
    """N-way merge should ignore empty streams gracefully."""
    a = [_entry("2026-01-01 10:00:00")]
    result = list(merge_n_streams([a, [], [], []]))
    assert result == a


def test_merge_n_many_streams():
    """Stress test: 10 streams, 10 entries each, all interleaved."""
    streams = []
    for i in range(10):
        streams.append([
            _entry(f"2026-01-01 10:{j:02d}:{i:02d}", source=f"s{i}")
            for j in range(10)
        ])
    result = list(merge_n_streams(streams))
    assert len(result) == 100
    times = [e.time for e in result]
    assert times == sorted(times)


def test_merge_two_result_is_fully_sorted():
    """Property test: output of merge_two is always sorted."""
    a = [_entry("2026-01-01 10:00:00"),
         _entry("2026-01-01 10:00:03"),
         _entry("2026-01-01 10:00:05")]
    b = [_entry("2026-01-01 10:00:01"),
         _entry("2026-01-01 10:00:02"),
         _entry("2026-01-01 10:00:04"),
         _entry("2026-01-01 10:00:06")]
    result = list(merge_two_streams(a, b))
    times = [e.time for e in result]
    assert times == sorted(times)
    assert len(result) == len(a) + len(b)
