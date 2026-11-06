import functools
import itertools
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from run import build, execute
from public_validate import check

SEED = 4130
rng = random.Random(SEED)
cases = []


def add(name, request, expected):
    cases.append({"name": name, "input": request, "output": expected})


def positions(text, pattern):
    return [i for i in range(len(text) + 1) if text.startswith(pattern, i)]


def lcs_length(a, b):
    for length in range(len(a), -1, -1):
        for indices in itertools.combinations(range(len(a)), length):
            candidate = "".join(a[i] for i in indices)
            iterator = iter(b)
            if all(any(c == value for value in iterator) for c in candidate):
                return length


@functools.lru_cache(None)
def merge_cost(sizes):
    if len(sizes) < 2:
        return 0
    return min(
        sizes[i] + sizes[i + 1]
        + merge_cost(sizes[:i] + (sizes[i] + sizes[i + 1],) + sizes[i + 2:])
        for i in range(len(sizes) - 1)
    )


def tree_weight(weights, edges):
    best = 0
    for mask in range(1 << len(weights)):
        if all(not (mask >> u & 1 and mask >> v & 1) for u, v in edges):
            best = max(best, sum(w for i, w in enumerate(weights) if mask >> i & 1))
    return best


def suffix_expected(text):
    sa = sorted(range(len(text)), key=lambda i: text[i:])
    lcp = [0] * len(text)
    repeated = ""
    for rank in range(1, len(text)):
        a, b = sa[rank - 1], sa[rank]
        common = 0
        while a + common < len(text) and b + common < len(text):
            if text[a + common] != text[b + common]:
                break
            common += 1
        lcp[rank] = common
        if common > len(repeated):
            repeated = text[a:a + common]
    return {"sa": sa, "lcp": lcp, "repeated": repeated}


def word(length):
    return "".join(rng.choice('abAB !~"\\') for _ in range(length))


def small_cases():
    for a, b in [("", ""), ("", "x"), ("x", ""), ("tea_time", "team"),
                 ("abab", "baba"), ("aaaa", "aa")]:
        add("lcs-boundary", {"task": "lcs", "a": a, "b": b},
            {"length": lcs_length(a, b)})
    for _ in range(100):
        a, b = word(rng.randrange(9)), word(rng.randrange(9))
        add("lcs-exhaustive", {"task": "lcs", "a": a, "b": b},
            {"length": lcs_length(a, b)})
    for sizes in [[], [7], [0, 0, 0], [1, 100, 1], [10**9] * 5]:
        add("merge-boundary", {"task": "merge", "sizes": sizes},
            {"cost": merge_cost(tuple(sizes))})
    for _ in range(100):
        sizes = tuple(rng.randrange(8) for _ in range(rng.randrange(8)))
        add("merge-all-orders", {"task": "merge", "sizes": list(sizes)},
            {"cost": merge_cost(sizes)})
    for weights in [[], [0], [-10], [10], [-1] * 8, [0] * 8]:
        edges = [[i - 1, i] for i in range(1, len(weights))]
        add("tree-boundary", {"task": "tree", "n": len(weights), "weights": weights,
                             "edges": edges}, {"weight": tree_weight(weights, edges)})
    for _ in range(100):
        n = rng.randrange(12)
        labels = list(range(n))
        rng.shuffle(labels)
        edges = [[labels[i], labels[rng.randrange(i)]] for i in range(1, n)]
        weights = [rng.randrange(-10, 11) for _ in range(n)]
        add("tree-all-subsets", {"task": "tree", "n": n, "weights": weights,
                                "edges": edges}, {"weight": tree_weight(weights, edges)})
    samples = [("", ""), ("", "a"), ("ab", "abcd"), ("abc", ""), ("aaaaa", "aaa"),
               ("abdj", "ab"), ("dj", "ab"), ("~ ab! ab", "ab"), ('a"\\a"\\', '"\\')]
    for _ in range(300):
        text = word(rng.randrange(70))
        pattern = word(rng.randrange(15))
        if text and rng.random() < 0.5:
            start = rng.randrange(len(text))
            pattern = text[start:start + rng.randrange(10)]
        samples.append((text, pattern))
    for text, pattern in samples:
        for task in ("naive", "kmp", "rk"):
            add("search-oracle", {"task": task, "text": text, "pattern": pattern},
                {"positions": positions(text, pattern)})
    for text in ["", "a", "aaaaa", "banana", "abcdef", "ababcdcd", " ~!"]:
        add("suffix-boundary", {"task": "suffix", "text": text}, suffix_expected(text))
    for _ in range(200):
        text = word(rng.randrange(70))
        add("suffix-direct-sort", {"task": "suffix", "text": text}, suffix_expected(text))
    dictionaries = [([], ["", "abc"]), (["a"], []), (["he", "she", "he"], ["sheshe"] * 2 + [""]),
                    (["a", "aa", "aaa", "a"], ["aaaaa", ""])]
    for _ in range(150):
        patterns = [word(rng.randrange(1, 8)) for _ in range(rng.randrange(15))]
        if patterns:
            patterns.append(patterns[0])
        dictionaries.append((patterns, [word(rng.randrange(70)) for _ in range(rng.randrange(6))]))
    for patterns, texts in dictionaries:
        add("aho-direct-counts", {"task": "aho", "patterns": patterns, "texts": texts},
            {"counts": [[len(positions(text, p)) for p in patterns] for text in texts]})


def scale_cases():
    add("lcs-million-cells", {"task": "lcs", "a": "ab" * 500, "b": "ba" * 500},
        {"length": 999})
    n = 200
    depth = n.bit_length() - 1
    add("merge-200-large", {"task": "merge", "sizes": [10**9] * n},
        {"cost": (n * depth + 2 * (n - 2**depth)) * 10**9})
    add("merge-200-zero", {"task": "merge", "sizes": [0] * n}, {"cost": 0})
    n = 100000
    add("tree-deep-chain", {"task": "tree", "n": n, "weights": [10**9] * n,
                           "edges": [[i - 1, i] for i in range(1, n)]},
        {"weight": n // 2 * 10**9})
    add("tree-large-star", {"task": "tree", "n": n, "weights": [10**9] * n,
                           "edges": [[0, i] for i in range(1, n)]},
        {"weight": (n - 1) * 10**9})
    for task, text, pattern in [
        ("naive", "a" * 3000, "a" * 1500),
        ("naive", "a" * 3000, "a" * 1499 + "b"),
        ("kmp", "a" * 200000, "a" * 100000),
        ("kmp", "a" * 200000, "a" * 99999 + "b"),
        ("kmp", "a" * 200000, ""),
        ("rk", "a" * 10000, "a" * 2000),
        ("rk", "a" * 10000, "a" * 1999 + "b"),
        ("rk", "x", "x" * 10000),
    ]:
        add("search-scale", {"task": task, "text": text, "pattern": pattern},
            {"positions": positions(text, pattern)})
    n = 50000
    add("suffix-all-equal", {"task": "suffix", "text": "a" * n},
        {"sa": list(range(n - 1, -1, -1)), "lcp": list(range(n)), "repeated": "a" * (n - 1)})
    text = "".join(rng.choice("abcd ") for _ in range(n))
    sa = sorted(range(n), key=lambda i: text[i:i + 64])
    assert all(text[a:a + 64] != text[b:b + 64] for a, b in zip(sa, sa[1:]))
    lcp = [0] * n
    for rank in range(1, n):
        a, b = sa[rank - 1], sa[rank]
        while a + lcp[rank] < n and b + lcp[rank] < n and text[a + lcp[rank]] == text[b + lcp[rank]]:
            lcp[rank] += 1
    add("suffix-large-random", {"task": "suffix", "text": text},
        {"sa": sa, "lcp": lcp, "repeated": "x" * max(lcp)})
    patterns = ["a" * 10] * 10000
    texts = ["a" * 2000] * 100
    add("aho-dense-duplicates", {"task": "aho", "patterns": patterns, "texts": texts},
        {"counts": [[1991] * 10000 for _ in texts]})
    patterns = ["a" * i for i in range(1, 447)]
    add("aho-suffix-chain", {"task": "aho", "patterns": patterns, "texts": ["a" * 200000]},
        {"counts": [[200001 - len(p) for p in patterns]]})
    pattern = "a" * 100000
    add("aho-max-depth", {"task": "aho", "patterns": [pattern], "texts": ["a" * 200000, ""]},
        {"counts": [[100001], [0]]})
    patterns = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10))
                for _ in range(10000)]
    add("aho-wide-trie", {"task": "aho", "patterns": patterns, "texts": [""] * 100},
        {"counts": [[0] * 10000 for _ in range(100)]})
    add("aho-no-patterns-100-texts", {"task": "aho", "patterns": [], "texts": ["a" * 2000] * 100},
        {"counts": [[] for _ in range(100)]})


def run_batch(command, batch, label):
    start = time.perf_counter()
    answers = execute(command, [case["input"] for case in batch])
    for case, answer in zip(batch, answers):
        if not check(case["input"], answer, case["output"]):
            raise AssertionError(f'{label}: {case["name"]}: {str(answer)[:300]}')
    elapsed = time.perf_counter() - start
    print(f"PASS {label}: {len(batch)} cases, {elapsed:.3f} s")


def main():
    command = build("Java")
    small_cases()
    small = cases.copy()
    run_batch(command, small + list(reversed(small)), f"independent oracles and mixed reset, seed={SEED}")
    cases.clear()
    scale_cases()
    for task in ("lcs", "merge", "tree", "naive", "kmp", "rk", "suffix", "aho"):
        run_batch(command, [case for case in cases if case["input"]["task"] == task], f"scale {task}")
    print(f"PASS all student checks: {len(small) * 2 + len(cases)} requests")


if __name__ == "__main__":
    main()
