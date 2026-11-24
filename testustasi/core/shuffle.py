"""The seeded shuffle (the JS port is shared/shuffle.js): every student sees the questions and the options in their own
order, and the same student always sees the same order (a reload, another phone, the server and the demo agree).

mulberry32 seeded with FNV-1a of "test:user:attempt"; Fisher-Yates. 32-bit integer arithmetic only, so Python and
JavaScript produce identical permutations."""

from __future__ import annotations

from .text import h32

M32 = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    return (a * b) & M32


class Rng:
    def __init__(self, seed: int) -> None:
        self.a = seed & M32

    def next(self) -> int:
        self.a = (self.a + 0x6D2B79F5) & M32
        a = self.a
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & M32) ^ t
        return (t ^ (t >> 14)) & M32


def perm(n: int, seed: int) -> list[int]:
    """A permutation of range(n): ``out[display position] = original index``."""
    out = list(range(n))
    rng = Rng(seed)
    for i in range(n - 1, 0, -1):
        j = rng.next() % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def attempt_seed(test: int, user: int, no: int) -> int:
    return h32(f"{test}:{user}:{no}")


def layout(qids: list[int], seed: int, shuffle: bool = True) -> list[dict]:
    """The order one attempt shows: [{"qid", "opts": [original option index per display position]}]."""
    order = perm(len(qids), seed) if shuffle else list(range(len(qids)))
    return [{"qid": qids[i], "opts": perm(4, h32(f"{seed}:{qids[i]}")) if shuffle else [0, 1, 2, 3]} for i in order]
