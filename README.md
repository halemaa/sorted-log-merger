# sorted-log-merger

Point this at multiple sorted log files. It produces one unified
timeline, in time order. Useful during incident investigation when
"what happened across all services at 09:15?" is the question.

Demonstrates **two-pointer merge** (for two files) and **N-way merge
with a min-heap** (for more than two). Both are one-pass algorithms —
no re-sorting of inputs.

## See it work

```bash
python generate_sample_logs.py      # creates nginx.log, app.log, auth.log
python merge.py nginx.log app.log auth.log
```

You'll see the three services' events interleaved in strict time
order:

```
2026-11-11 09:00:00  app    exception in request handler
2026-11-11 09:00:01  nginx  GET /health 200
2026-11-11 09:00:05  nginx  GET /api/users 200
2026-11-11 09:00:06  auth   user halemaa logged in
2026-11-11 09:00:06  nginx  GET /api/users 200
2026-11-11 09:00:08  nginx  GET /api/products 200
2026-11-11 09:00:10  app    queued background job #12
...
```

Three separate files → one chronological timeline. During an
incident this is the view that lets you spot "the database error
happened 2 seconds before all those 500s started."

## Use it on real logs

```bash
python merge.py access.log app.log auth.log
python merge.py access.log app.log --output merged.log
python merge.py *.log --show-source   # prefix each line with source file
```

Any log file whose lines start with a timestamp like
`2026-11-11 09:15:12` or `2026-11-11T09:15:12` works. Lines that
don't start with a timestamp are skipped silently.

## What's in the box

```
merger.py                   core: parsing + two-way merge + N-way merge
merge.py                    CLI
generate_sample_logs.py     writes nginx/app/auth sample logs
tests/test_merger.py        12 passing tests
theory/                     four beginner-level notes
```

## How it works, briefly

### Two files — two pointers

Each log file is already sorted (because timestamps are appended in
real time). We keep one pointer per file. At each step we look at
the current entry in each file, take the earlier one, and advance
that pointer. When one file runs out, we dump the rest of the
other. One pass each. O(n + m) time.

### Three or more files — a min-heap

With more than two files, "which is the smallest among all current
entries?" becomes a question itself. A **min-heap** (priority queue)
answers it in O(log k) time, where k is the number of files. Keep
one entry per file in the heap. Always take the smallest. Replace it
with the next entry from the same file. Repeat.

Total time: O(n × log k) where n is total entries. For 10 files,
`log k ≈ 3.3`, so the overhead is tiny.

## Read the theory

1. [What two pointers really is](theory/01-two-pointers.md) — the
   pattern you need to really get
2. [Merging two sorted things](theory/02-merging-two-sorted.md) —
   walked through with real log timestamps
3. [Going from 2 to N files](theory/03-n-way-merge-with-heap.md) —
   what a heap is, in plain words, and why we need one
4. [Where this shows up](theory/04-real-world-uses.md) — merge sort,
   database joins, big data pipelines

## Extending

- **Live tail mode** — `tail -f` multiple log files simultaneously
  and emit the merged live stream
- **Filtering** — `--grep ERROR` only passes through matching lines
- **Time window** — `--since 09:15 --until 09:20`
- **JSON output** — emit each entry as JSON for piping into other
  tools (jq, Splunk, Elasticsearch)
- **Compressed logs** — handle `.gz` files transparently
- **Guess the format** — auto-detect common log formats (nginx
  Combined, Apache, syslog) instead of requiring ISO timestamps

## Caveats

- Input files MUST be already sorted by timestamp. Most log files
  are, because events get appended in order. If they're not, sort
  each file first with `sort -o file.log file.log`.
- Lines without a parseable timestamp at the start are silently
  skipped. Pass `--strict` to make unrecognised lines an error
  (not implemented — would be a good extension).
- Memory usage is bounded regardless of file size: we never load a
  whole file, we stream.
