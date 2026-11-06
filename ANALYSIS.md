# Assignment 4 — analysis

## Environment and commands

The implementation targets Java 17. Local measurements used Oracle JDK 25.0.1, Python 3.14.3 and Windows on an Intel Core i5-11400H at 2.70 GHz. The Java heap limit was 384 MiB. Hardware RAM could not be queried in the restricted environment. GitHub Actions uses Temurin 17, Python 3.12 and Ubuntu 24.04.

Commands from the repository root:

    python tools/run.py --setup
    python tools/run.py --check
    python tests/student/check.py
    javac --release 17 -encoding UTF-8 -cp Java/build -d Java/build tests/student/SearchBenchmark.java
    java -Xmx384m -cp Java/build SearchBenchmark

On this machine the installed JDK was selected in PowerShell before running these commands:

    $env:PATH = 'C:/Program Files/Java/jdk-25/bin;' + $env:PATH

For a request file, use: python tools/run.py --input requests.jsonl. The launcher compiles with --release 17 and runs Main with -Xmx384m. JSON parsing and serialization are outside the algorithm complexity bounds below. Strings are printable ASCII. Costs, total weights, hashes and counts use long. Each request creates fresh task state.

## LCS

dp[i][j] is the maximum common subsequence length of the first i characters of a and first j characters of b. Empty prefixes have value zero. Equal final characters extend dp[i-1][j-1]; otherwise take the maximum of dp[i-1][j] and dp[i][j-1]. Increasing rows and columns make dependencies ready.

For unequal final characters a common subsequence cannot match both of them to each other, so an optimum lies in at least one shorter-prefix problem. For equal characters an optimum can end with that character. Induction on prefix sizes proves the recurrence.

Reconstruction starts at the last cell. Equal characters are appended while moving diagonally. A mismatch moves to a neighbour with the same optimal value; ties prefer the previous row. Reversing the collected characters produces an optimal subsequence of both strings.

For lengths a and b, time and auxiliary storage are O((a+1)(b+1)); reconstruction takes O(a+b). Input storage is O(a+b+1) and output is O(min(a,b)+1). Empty strings return zero and an empty sequence. The tea_time/team test distinguishes subsequences from substrings.

## Ordered merging

dp[l][r] is the minimum cost to merge the original closed interval [l,r]. A singleton costs zero. Prefix sums give each interval size in constant time. For every last split k, try dp[l][k] + dp[k+1][r] + prefix[r+1] - prefix[l].

The last merge joins two adjacent intervals at some k. Both subplans must be optimal, since replacing a more expensive subplan would improve the whole plan. Trying all splits therefore finds an optimum. Increasing interval lengths make subproblems ready. The first minimizing split is retained.

Reconstruction emits the left subplan, then the right, then [l,k,r]. Both child blocks therefore exist before their parent merge, and original indices remain valid. Recursion depth is at most 200. Empty and singleton inputs need no merges.

Time is O(n^3) and auxiliary memory O(n^2) for nonempty input; both are constant for no blocks. The O(n) reconstruction stack is within that bound. Input and output each need O(n+1) space. The [1,100,1] case rejects arbitrary nonadjacent merging. Billion-sized blocks test 64-bit costs.

## Tree independent set

An iterative traversal roots the tree at vertex zero and records every parent before its children. Reversing that order makes child results ready. take[v] is the optimum in the subtree when v is selected; skip[v] is the optimum when v is excluded.

take[v] = weight[v] + sum(skip[child]); skip[v] = sum(max(take[child], skip[child])). Different child subtrees have no edges between them. Selecting v excludes each child, while excluding v leaves the child decision unrestricted. These facts prove the transitions by induction from leaves. The root answer is the larger state; zero skip values allow the empty set.

Reconstruction scans the forward order. A selected parent forces its child to be excluded. Otherwise select the child only when its take state is strictly better. Ties choose exclusion. Each vertex is processed once, so the result is independent and has the optimum weight.

Primitive adjacency arrays give O(n+1) time and auxiliary memory, including reconstruction. Input and output also use O(n+1). No tree recursion is used. A chain of 100,000 vertices checks depth safety; a large star checks a total of 99,999,000,000,000. Negative and zero weights test empty solutions.

## Naive search

Every start from zero through n-m, inclusive, is compared character by character. A start is reported exactly when all characters agree. Advancing by one preserves overlaps. For an empty pattern the inner loop succeeds immediately at all n+1 boundaries; an overlong pattern gives no iterations.

Time is O(n*m+n+1), auxiliary memory O(1), input storage O(n+m+1) and output storage O(z+1). The aaaaa/aaa case requires starts 0, 1 and 2; empty inputs check the final boundary.

## KMP

prefix[i] is the longest proper prefix of the pattern that is also a suffix of its prefix ending at i. Entries are built left to right. A mismatch follows prefix[j-1], trying the next possible border. This enumerates exactly the remaining candidates.

While scanning text, matched is the length of the pattern prefix matching the text suffix already read. Mismatches follow the border chain without moving the text position backward. A full match reports its start and falls back to prefix[m-1], preserving overlaps. Empty patterns are handled before indexing.

Successful extensions increase the matched length by at most one per character; fallbacks decrease it. This amortized argument applies to both construction and searching. Time is O(n+m+z+1), auxiliary memory O(m+1), input storage O(n+m+1) and output storage O(z+1). Repetitive near-misses test fallback. An empty pattern on a 200,000-character text tests all boundaries.

## Exact Rabin–Karp

Hashes use ASCII codes, base 31 and modulus 101, with the highest power on the left. Let power = 31^(m-1) mod 101. Remove text[start]*power modulo 101, adding 101 before the remainder, then multiply by 31 and add the incoming character. The result is the polynomial hash of the next window.

Unequal hashes imply unequal strings. Equal hashes are only candidates: every candidate is compared character by character. Thus collisions cannot produce false matches. For abdj/ab only start zero is accepted, although ab and dj both hash to 75. Random punctuation cases exercise negative-remainder normalization.

Empty and overlong patterns are handled before forming a window. For 1 <= m <= n, time is O(n+m+c*m), where c is the number of equal-hash windows. A bound covering all inputs is O(n*m+n+m+1); deterministic linear worst-case time is not claimed. Auxiliary memory is O(1), input storage O(n+m+1) and output storage O(z+1).

## Suffix array and Kasai LCP

Initially ranks are character codes. Each doubling round sorts suffix starts by (rank[i], rank[i+width]), with -1 past the end. These pairs represent prefixes twice as long. Distinct sorted pairs receive distinct new ranks. Induction on width proves that ranks describe prefix order. Once all ranks differ or the width covers the string, this is full suffix order.

Only original positions are sorted: no sentinel or empty suffix is emitted. Integer[] and Arrays.sort use comparison sorting with constant-time rank comparisons. Each round costs O(n log(n+1)), giving O(n log^2(n+1)) total time. Rank arrays, boxed starts and sort workspace use O(n+1) auxiliary memory. Suffix strings are not materialized.

Kasai builds inverse suffix positions. Each original start is compared with its previous sorted suffix. After advancing one character, the reusable common-prefix lower bound decreases by at most one. It is reset to zero at the first ranked suffix. Total successful increments are O(n), so Kasai takes O(n) time with O(n+1) storage; lcp[0] is zero.

Suffixes sharing a prefix form a contiguous sorted range. Consequently some adjacent pair has that common prefix, and the maximum adjacent LCP gives a longest repeat. Only a strictly longer result replaces the saved choice, so any tied optimum is valid. Overlapping occurrences are allowed.

Input and output each use O(n+1) space. Empty input returns empty arrays and an empty repeat. All-equal input tests long overlapping repeats, and distinct characters test an empty repeated string.

## Aho–Corasick

One trie is built per request with 95 transitions per actual state. Terminal IDs are retained in dictionary order, so duplicates share a terminal. Breadth-first processing creates failure links and fills missing transitions from the already completed failure-state transition.

A failure link points to the longest proper suffix that is also a trie prefix. After reading a character, the state represents the longest dictionary prefix matching the current text suffix. Each visited state gets one count. Reverse breadth-first processing adds each state's count to its failure state. Thus every suffix-pattern terminal receives precisely its occurrence count, including overlaps, without enumerating individual matches.

Each text starts at the root with a new long[] visit array. Reading terminal counts in dictionary order gives equal columns for duplicates. Empty texts have zero counts; an empty dictionary produces an empty row per text; no texts produces no rows.

For total pattern length L, actual states S, dictionary size p and q texts, construction takes O(L+95*S+p) time and O(95*S+p) auxiliary memory. Transition rows are allocated only for actual states using an ArrayList; failure and visit arrays are sized to S. Each text costs O(|text|+S+p). Input storage is O(L+sum(|text|)+p+q+1), and output storage O(q*(p+1)+1).

Dense duplicates and nested suffix patterns test aggregation. A pattern of length 100,000 tests depth without recursion; a wide trie queried with 100 empty texts tests many states and resets.

## Own tests

tests/student/check.py uses seed 4130. Small-input oracles independently enumerate subsequences, adjacent merge orders and vertex subsets; string matching uses startswith, and suffixes are sorted directly. The public validator also checks witnesses and numeric types.

There are 1,605 small cases, run forward and backward in one process for 3,210 requests, plus 20 scale cases in task-specific batches. Scale expectations use known constructions. For the large random suffix test, 64-character prefixes are sorted and asserted unique, which makes their order the full suffix order; LCP is then computed directly.

| Command | Fixture in tests/student/check.py | Expected result | Actual | Defect checked |
|---|---|---|---|---|
| lcs | small_cases, scale_cases | exhaustive optimum; alternating scale case length 999 | PASS | empty inputs, ties, subsequences |
| merge | small_cases, scale_cases | exhaustive cost; 200 equal large blocks cost 1,544,000,000,000 | PASS | adjacency, chronology, overflow |
| tree | small_cases, scale_cases | exhaustive optimum; chain weight 50,000,000,000,000 | PASS | witnesses, negative weights, depth |
| naive | search-oracle, search-scale | exact oracle starts | PASS | overlaps, final boundary |
| kmp | search-oracle, search-scale | exact starts; 100,001 maximum-length matches | PASS | fallback, state reset |
| rk | search-oracle, search-scale | collision rejected; oracle starts | PASS | hash collisions, remainder |
| suffix | suffix-direct-sort, suffix-large-random, suffix-all-equal | exact SA/LCP; equal-input repeat length 49,999 | PASS | order, sentinel, LCP reuse |
| aho | aho-direct-counts and scale fixtures | direct counts; every dense duplicate count 1,991 | PASS | suffixes, duplicates, reset, scale |

The first full local run passed 3,230 student requests. Observed batch wall times, including startup, JSON transport and validation: LCS 0.134 s, merge 0.121 s, tree 0.656 s, naive 0.170 s, KMP 0.370 s, RK 0.177 s, suffix 0.358 s, Aho–Corasick 1.030 s. The small mixed batch took 0.324 s. All 44 public cases and the repeated 88-request batch passed. These observations do not guarantee unpublished test results.

## Search comparison

The runnable benchmark is tests/student/SearchBenchmark.java. [Raw times and medians](tests/student/benchmark-results.md) record all three measured runs per case. All algorithms receive identical strings at n = 500, 1500, 3000, with m = n/10, within their common domain.

Random text uses Java Random(4130+n) with uniform lowercase letters. The pattern is the length-m substring starting at n/2, guaranteeing a match. Repetitive text is n copies of a; its pattern is m-1 copies of a followed by b, giving no matches. The recorded seed is unused for repetitive cases.

Before timing, an independent String.startsWith oracle verifies every result, including the RK collision. All algorithms and fixtures are warmed up for 1,000 rounds in the same JVM. Three runs then average 100 calls each; algorithm order rotates between runs. System.nanoTime measures the algorithm, preprocessing, result construction and a volatile sink assignment. Compilation, input generation, checks, JSON and printing are excluded equally. Units are microseconds per call. Garbage collection is not forced; normal JIT and OS noise remains.

Random-input medians for increasing sizes were: naive 1.669, 6.641, 14.418 us; KMP 1.346, 4.737, 10.278 us; RK 4.735, 12.722, 29.453 us. Early naive mismatches keep it competitive; modular arithmetic adds RK overhead.

Repetitive near-miss medians were: naive 54.566, 436.980, 1,913.206 us; KMP 2.904, 8.086, 18.149 us; RK 4.328, 11.843, 24.940 us. Naive repeats nearly full comparisons, while KMP reuses borders. These particular repetitive RK windows have a different hash from the pattern and are rejected cheaply; this is not a worst-case guarantee.

The deliberately small modulus can generate many equal-hash candidates on other inputs. Dense true matches also require character verification. These measurements describe this generator and runtime, not a proof of asymptotic bounds or a general claim about production hashing.

## Sources

The [official template](https://github.com/RZhaniya/daa-assignment-4-archive/tree/4686cc60334aa189c2ac168e10a82d882b32858c) supplied contracts, public cases, the Python launcher, public validator and JSON transport. The required recurrences and construction methods follow the assignment contracts. Verification used published cases, independent small-input oracles, witness validation and maximum-domain tests described above.
