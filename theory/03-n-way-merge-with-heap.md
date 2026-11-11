# 3 — Going from 2 files to N files (what a heap is)

## The problem

Two-pointer merge works great for **two** files. What if you have
three? Or ten?

Say you have nginx.log, app.log, auth.log, and syslog. At each step
you need to find the smallest-timestamp entry among **four**
candidates, not two.

Naive approach: scan through all four, find the smallest, advance
that one. That's 4 comparisons per step. For 10 files it's 10
comparisons per step. For 100 files it's 100 comparisons per step.

In Big-O terms: `O(n × k)` where k is the number of files.

We can do better. We can get it down to `O(n × log k)`. The tool to
get us there is called a **heap** (or **priority queue**).

## What a heap actually is

A heap is a container that answers one question very fast: *"what's
the smallest thing in here right now?"*

That's it. You put things in. Any time you ask "give me the
smallest," it hands you the smallest, in `O(log k)` time instead of
scanning all k items.

Think of it as a **"self-sorting bucket"** that always knows which
item is smallest, no matter how many items it holds.

## The physical analogy

Imagine a shop with 10 waiting customers, each with a number ticket.
You want to serve them in ticket-number order (smallest number
first).

**Naive way:** every time you're ready to serve someone, you shout
"who has the smallest number?" and look at every customer's ticket.
10 comparisons each round.

**Heap way:** you have a special queue that keeps itself ordered.
Every time someone enters, the queue reshuffles so the smallest
number is always at the front. You just serve the front.

The "reshuffling" costs a little bit (that's where `log k` comes
from), but it's much faster than re-scanning every time.

## How the N-way merge uses it

Walk through 4 log files:

**Setup.** Take the first entry from each file. Put all four in the
heap.

```
Heap:
  09:00:00  app
  09:00:01  nginx
  09:00:06  auth
  09:00:09  syslog
```

The heap has reshuffled itself so `09:00:00 app` is at the front.

**Round 1.** Pull `09:00:00 app` from the heap. Emit it to output.
Fetch the NEXT entry from app.log — say it's `09:00:10 app` — and
put that in the heap.

```
Heap (after):
  09:00:01  nginx     ← new front
  09:00:06  auth
  09:00:09  syslog
  09:00:10  app
```

The heap reshuffled again. New front is `09:00:01 nginx`.

**Round 2.** Pull nginx. Emit. Fetch next from nginx.log. Put in heap.

And so on. Every round: pull the smallest, emit it, refill its slot
from the stream it came from.

**When a stream runs out:** don't refill its slot. The heap shrinks
by one. Eventually the heap is empty. Done.

## Why this is fast

Each log entry enters the heap once and leaves once. Both operations
cost `O(log k)` where k is the current heap size.

Total work: `O(n × log k)` where n is total entries and k is the
number of files.

For 10 files, `log k ≈ 3.3`. So merging 1 million entries across 10
files costs ~3.3 million operations instead of ~10 million (naive)
or ~20 million (full sort). The heap pays for itself quickly.

## Python already has one — `heapq`

Python's standard library includes `heapq`, which operates on a
regular list:

```python
import heapq

heap = []
heapq.heappush(heap, (5, "five"))
heapq.heappush(heap, (1, "one"))
heapq.heappush(heap, (3, "three"))

print(heapq.heappop(heap))    # (1, "one")  — smallest comes out first
print(heapq.heappop(heap))    # (3, "three")
print(heapq.heappop(heap))    # (5, "five")
```

The list still looks like a list. `heapq` just maintains the
"always knows the smallest" property internally.

By default heaps are **min-heaps** (smallest first). That's exactly
what we want for "earliest timestamp first."

## The actual N-way merge code

From `merger.py`:

```python
import heapq

def merge_n_streams(streams):
    iters = [iter(s) for s in streams]

    # Prime the heap: one entry per stream.
    heap = []
    for i, it in enumerate(iters):
        entry = next(it, None)
        if entry is not None:
            heapq.heappush(heap, (entry.time, i, entry))

    while heap:
        _, i, entry = heapq.heappop(heap)
        yield entry                  # emit the earliest
        next_entry = next(iters[i], None)   # refill from the same stream
        if next_entry is not None:
            heapq.heappush(heap, (next_entry.time, i, next_entry))
```

Two things to notice:

### 1. Tuples in the heap

We don't put raw LogEntry objects in the heap — we put
`(time, index, entry)` tuples. Python compares tuples
element-by-element, so it sorts by `time` first. The `index` is a
tiebreaker — if two entries have the same timestamp, the one with
the smaller stream index wins. That makes the output stable and
avoids Python trying to compare `LogEntry` objects (which it
wouldn't know how to do).

### 2. Refilling the same stream

When we pop an entry from the heap, we also pop information about
*which stream it came from* (the index `i`). We use that to fetch
the next entry from the SAME stream and put it back in the heap.

That's what keeps all streams moving at once: whichever stream is
contributing the "currently smallest" item, we pull one more from
it.

## Special case: what if two streams run out?

The `if next_entry is not None:` check means: when a stream is
exhausted, we don't push a new entry. The heap just gets smaller.
Eventually it's empty and the loop ends. Clean.

## Why not just do two-pointer merge pair-by-pair?

You CAN merge files pair by pair:

```python
result = merge_two(a, b)
result = merge_two(result, c)
result = merge_two(result, d)
```

But every call re-walks the growing result. Total work: `O(n × k)` —
same as naive. The heap approach is strictly better for k ≥ 3.

For **exactly 2** files though, two-pointer merge has no heap
overhead and is slightly faster in practice. That's why our tool
picks `merge_two_streams` for k=2 and `merge_n_streams` for k≥3.

## The one-paragraph summary

> A heap is a container that always knows its smallest element in
> O(log k) time. For N-way merge, put one item per stream in the
> heap. Repeatedly pop the smallest, emit it, and refill from the
> stream it came from. Total time O(n × log k), which beats the
> naive O(n × k) scan for anything more than a couple of streams.

Remember two things: **a heap answers "what's smallest?" fast**, and
**that's exactly what N-way merge needs on every step.** The rest
follows.
