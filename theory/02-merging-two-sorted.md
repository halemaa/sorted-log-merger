# 2 — Merging two sorted things, step by step

## The setup

You have two log files. Each is sorted by timestamp (because log
lines get appended as events happen — natural sort order).

**nginx.log:**
```
09:00:01  GET /health
09:00:05  GET /api/users
09:00:08  GET /api/products
09:00:14  POST /api/orders
```

**app.log:**
```
09:00:00  exception in request handler
09:00:10  queued background job
09:00:11  database connection established
```

You want **one merged stream** showing everything in chronological
order:

```
09:00:00  app    exception in request handler
09:00:01  nginx  GET /health
09:00:05  nginx  GET /api/users
09:00:08  nginx  GET /api/products
09:00:10  app    queued background job
09:00:11  app    database connection established
09:00:14  nginx  POST /api/orders
```

## The naive approach

Dump everything into one pile. Sort from scratch.

- Combine → 7 entries
- Sort → ~7 × log(7) ≈ 20 operations

**Wasteful.** We just did a full sort on data that was already
mostly sorted. We ignored the thing we knew.

## The two-pointer way

Keep one bookmark in each file. Repeatedly: look at where both
bookmarks are, pick the earlier one, advance that bookmark.

Let's trace it.

### Setup

```
nginx.log         app.log
09:00:01   ← N    09:00:00   ← A
09:00:05          09:00:10
09:00:08          09:00:11
09:00:14
```

Pointer N at top of nginx. Pointer A at top of app. Output is empty.

### Round 1

N shows `09:00:01`. A shows `09:00:00`. **A is earlier.** Take A.
Advance A.

```
Output: [09:00:00 app exception]
nginx.log         app.log
09:00:01   ← N    09:00:10   ← A
09:00:05          09:00:11
09:00:08
09:00:14
```

### Round 2

N: `09:00:01`. A: `09:00:10`. **N is earlier.** Take N. Advance N.

```
Output: [09:00:00 app, 09:00:01 nginx GET /health]
nginx.log         app.log
09:00:05   ← N    09:00:10   ← A
09:00:08
09:00:14
```

### Round 3

N: `09:00:05`. A: `09:00:10`. N wins. Take N.

```
Output: [..., 09:00:05 nginx GET /api/users]
```

### Round 4

N: `09:00:08`. A: `09:00:10`. N wins.

```
Output: [..., 09:00:08 nginx GET /api/products]
```

### Round 5

N: `09:00:14`. A: `09:00:10`. **A is earlier now.** Take A.

```
Output: [..., 09:00:10 app queued background job]
nginx.log         app.log
09:00:14   ← N    09:00:11   ← A
```

### Round 6

N: `09:00:14`. A: `09:00:11`. A wins.

```
Output: [..., 09:00:11 app database connection established]
nginx.log         app.log
09:00:14   ← N    (empty)
```

### Round 7 — special case: one file is empty

App is empty. There's nothing to compare against. **Just dump the
rest of nginx.**

```
Output: [..., 09:00:14 nginx POST /api/orders]
```

Both files done. Total operations: 7 (one per element taken).

## Count the work

- Naive: ~20 operations (sort from scratch)
- Two-pointer: 7 operations (one per element)

Three times faster even on this tiny example. On a million-line log
file the naive approach does ~20 million operations; two-pointer
does 1 million. **Twenty times faster.**

## The code

Here's the algorithm in Python, straight from `merger.py`:

```python
def merge_two_streams(a, b):
    iter_a = iter(a)
    iter_b = iter(b)
    cur_a = next(iter_a, None)   # get the first item from each
    cur_b = next(iter_b, None)

    while cur_a is not None and cur_b is not None:
        if cur_a.time <= cur_b.time:
            yield cur_a             # take the earlier one
            cur_a = next(iter_a, None)   # advance that pointer
        else:
            yield cur_b
            cur_b = next(iter_b, None)

    # One stream is done — drain the other.
    while cur_a is not None:
        yield cur_a
        cur_a = next(iter_a, None)
    while cur_b is not None:
        yield cur_b
        cur_b = next(iter_b, None)
```

Read it alongside the walkthrough. Every line maps to something we
did by hand.

## One subtlety — stable ordering

Two entries might have the exact same timestamp. What then?

Our code uses `<=` (not `<`) when comparing:

```python
if cur_a.time <= cur_b.time:
```

The `=` means: "when they're equal, prefer A." This is **stable
ordering** — events from file A always come before events from file
B when their timestamps tie. It makes output predictable.

If we'd used `<` instead, ties would go to B. Either works; what
matters is that we pick one and stick with it.

## Why does this only work on sorted input?

The whole trick is "take the smaller one, advance that pointer." If
the input weren't sorted, "smaller one here" doesn't mean "smaller
one overall." You'd miss things.

Example of failure on unsorted input:

```
a.log     b.log
09:00:05  09:00:03
09:00:02  09:00:08
```

Round 1: `09:00:05 vs 09:00:03`. Take `09:00:03`. Advance b.
Round 2: `09:00:05 vs 09:00:08`. Take `09:00:05`. Advance a.
Round 3: `09:00:02 vs 09:00:08`. Take `09:00:02`. Advance a.

Output: `[09:00:03, 09:00:05, 09:00:02, 09:00:08]` — not sorted.

That's why the README warns: your input files must be sorted first.
Luckily, real log files already are.

## The one-sentence summary

> Two pointers, one per sorted stream, always advance the one with
> the smaller current element. One pass through each. O(n + m).

Memorise that sentence. You'll use it for the rest of your career.
