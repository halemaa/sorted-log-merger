# 1 — What two pointers really is

## Start with "pointer"

Forget the computer-science word for a second. A **pointer** is just
a bookmark. A number telling you where you are in a list.

If you're reading a book and your finger holds your place at page
47, your finger is a pointer. "I'm currently at position 47."

In code, that's just an index — a number like `i = 5` saying "I'm
currently at position 5 in this list."

```python
books = ["Alice", "Bob", "Clara", "Daniel"]
#          0        1       2        3
#                            ↑
#                      pointer i = 2
```

Nothing magical. Just a number pointing at a position.

## Why "one pointer" isn't a thing

Walking through a list with one pointer is... a normal loop. We do
this all day:

```python
for i in range(len(books)):
    print(books[i])
```

No special name for it. It's just reading a list.

## Why "two pointers" IS a thing

Two pointers means **two bookmarks moving at the same time, each
with its own rules**. That's where the technique gets powerful —
because you can solve certain problems in a *single* pass that
otherwise would need nested loops.

The three common patterns:

### Pattern 1 — opposite ends

Pointers start at both ends of a list and move toward each other.

> *Example: is "madam" a palindrome?*
> One finger at the first letter, one at the last. Compare them,
> then step inward. If they ever disagree, not a palindrome. If
> they meet in the middle, it is one.

Classic uses: palindrome check, two-sum on a sorted array, container
with most water.

### Pattern 2 — fast and slow

Pointers both move forward but at different speeds.

> *Example: remove duplicates from a sorted list in place.*
> A "scanner" finger walks every step. A "writer" finger lags
> behind and only moves when it writes something. The writer ends
> up marking off the unique section.

Classic uses: removing duplicates, cycle detection in linked lists,
finding the middle of a list.

### Pattern 3 — one in each of two lists (THIS PROJECT)

Each pointer walks a different list. They advance independently
based on what they see.

> *Example: merge two sorted stacks of cards.*
> One finger on top of each stack. Compare the cards. Take the
> smaller one. Move that finger. Repeat.

Classic uses: merging sorted sequences, database joins, playlist
interleaving, log file merging.

## The property all three share

**Each pointer only goes forward.** A pointer never jumps backwards
or skips around. It walks in one direction, driven by the current
state of the data.

That's what makes two-pointer algorithms O(n). Every element gets
visited at most a constant number of times (once per pointer that
touches it). No nested loops. One pass.

## The data structure is the same — the pointers do the work

A two-pointer algorithm doesn't change the underlying data. It just
walks through it with two bookmarks and reads cleverly. The lists
are regular lists. The pointers are regular integers.

So when you hear someone say "I used a two-pointer approach," they
mean: "I walked through the data with two position-trackers,
advancing them based on what I saw, instead of looping over it
twice."

## Why "this works" — the sorted-data secret

Two-pointer tricks almost always require sorted input. That's not a
coincidence.

When data is sorted, you know something strong:
- If the current element at pointer A is smaller than at pointer B,
  then **every** element before A is also smaller than at B.
- You can use that fact to decide which pointer to move, with
  confidence that you're not missing anything.

Unsorted data breaks this promise. You'd need to look at every
element again every time, which is why unsorted versions of these
problems are O(n²) instead of O(n).

**Sortedness turns O(n²) into O(n).** Two pointers is the technique
that collects the payment.

## The habit to build

Whenever you're facing a problem about sorted data where you want to
compare, merge, or find pairs — reach for two pointers before you
reach for nested loops. Nine times out of ten, the two-pointer
version is shorter, faster, and the one a senior engineer would
write.

Next note walks through the merge algorithm specifically, step by
step, with real log timestamps.
