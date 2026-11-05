"""Read every passage of a chunked literature corpus with Claude, for one question.

A top-k search reads the passages most like the question. An answer spread over hundreds of
papers is mostly in passages that do not look like the question, so this reads all of them:
Claude gets every passage, ten at a time, as numbered sentences, and returns the numbers of the
sentences that bear on the question. The sentences are then taken from the text by number, so a
quote cannot be invented.

    python read_corpus.py estimate --chunks chunks.jsonl --question "..."
    python read_corpus.py read --chunks chunks.jsonl --question "..." --out DIR [--manifest manifest.csv]
    python read_corpus.py genes --evidence DIR/evidence.csv --hgnc hgnc_complete_set.txt

``chunks.jsonl`` holds one passage per line: ``{"pmid": ..., "chunk": ..., "page": ..., "text": ...}``.
``read`` needs the ``anthropic`` package and ``ANTHROPIC_API_KEY`` (``ANTHROPIC_BASE_URL`` for a
proxy). It writes ``evidence.csv`` (every passage that bears on the question, with its sentences),
``read_log.csv`` (every passage and whether it was read) and ``usage.json`` (calls, tokens, cost,
time). Each batch is appended to ``reads.jsonl`` as it finishes, so a run that stops is resumed by
running the same command again; passages that failed are read again then.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

MODEL = "claude-haiku-5-5"
EFFORT = "medium"
BATCH = 10
WORKERS = 48
MAX_TOKENS = 8000
PRICE_IN, PRICE_OUT = 0.10, 0.50  # USD per million tokens, Claude Haiku 5.5
CORPUS = "the lab's RetiGene corpus (inherited retinal disease)"

# Measured on two whole reads of the 39,563-passage RetiGene corpus (Claude Haiku 5.5, effort
# medium, 10 passages a call): characters sent per input token, output tokens per passage (the
# two questions), and seconds per call per parallel worker (48 workers, no rate limiting).
CHARS_PER_TOKEN = 2.3
OUT_PER_PASSAGE = (73, 109)
SECONDS_PER_CALL = 4.8

READ_SYSTEM = (
    "You read passages from research papers in {corpus} for "
    "one question. For EACH passage, list the numbers of the sentences that bear on the question: that "
    "state a finding, a claim, an observation, a method or a negative result about what it asks. Judge "
    "only from the text given, never from what you know. A passage that names the subject only in "
    "passing (a reference list, an author list, a list of genes with nothing said about the one asked "
    "about, a heading) bears on nothing.\n"
    'Reply with ONLY one JSON object: {{"passages": [{{"id": "P1", "sentences": [3, 4], "note": "what '
    'they say about the question, at most 25 words"}}, ...]}}, with one entry for EVERY passage given and '
    '"sentences": [] for a passage that bears on nothing.'
)

Call = Callable[[list[dict]], "tuple[str, dict]"]

# ---- passages ------------------------------------------------------------------------------------

_ABBR = re.compile(
    r"\b(?:et al|Fig|Figs|Dr|vs|e\.g|i\.e|cf|approx|No|Ref|Refs|Suppl|Tab|ca)\.$", re.I
)
_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\(\[“\"])")


def split_sentences(text: str) -> list[str]:
    """The passage as sentences: split after a full stop, a question or an exclamation mark before a
    capital, a digit or an opening bracket, never after a common abbreviation."""
    parts = _SPLIT.split(" ".join(str(text or "").split()))
    out: list[str] = []
    for part in parts:
        if out and _ABBR.search(out[-1]):
            out[-1] = f"{out[-1]} {part}"
        else:
            out.append(part)
    return [s.strip() for s in out if s.strip()]


def load_passages(path: Path) -> list[dict]:
    """Every passage with text, in file order, keyed ``pmid:chunk``; a repeated key is kept once."""
    out: list[dict] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            text = str(row.get("text") or "")
            pmid = str(row.get("pmid") or "").strip()
            key = f"{pmid}:{row.get('chunk')}"
            if not pmid or not text.strip() or key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "key": key,
                    "pmid": pmid,
                    "chunk": row.get("chunk"),
                    "page": row.get("page"),
                    "sentences": split_sentences(text),
                }
            )
    return out


def load_manifest(path: Path | None) -> dict[str, dict]:
    """PMID -> citation, title and year, from a manifest CSV with a ``doc_id`` or ``pmid`` column."""
    if not path:
        return {}
    out: dict[str, dict] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            pmid = str(row.get("pmid") or row.get("doc_id") or "").strip()
            if pmid:
                out[pmid] = {k: row.get(k) or "" for k in ("citation", "title", "year")}
    return out


# ---- one call --------------------------------------------------------------------------------------


def read_messages(question: str, batch: list[dict], corpus: str = CORPUS) -> list[dict]:
    blocks = []
    for i, p in enumerate(batch, 1):
        head = f"P{i} — PMID {p['pmid']}" + (
            f", p. {p['page']}" if p["page"] not in (None, "") else ""
        )
        blocks.append(
            head + "\n" + "\n".join(f"[{n}] {s}" for n, s in enumerate(p["sentences"], 1))
        )
    return [
        {"role": "system", "content": READ_SYSTEM.format(corpus=corpus)},
        {"role": "user", "content": f"Question: {question}\n\n" + "\n\n".join(blocks)},
    ]


def json_object(text: str) -> dict | None:
    """The JSON object in a reply: the whole reply (``json`` fences allowed), else the outermost
    braces in it."""
    s = str(text or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s[4:].strip() if s.lower().startswith("json") else s
    for candidate in (s, (re.search(r"\{.*\}", s, re.DOTALL) or [""])[0]):
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


def parse_read(raw: str, batch: list[dict]) -> dict[int, tuple[list[int], str]] | None:
    """Passage position (0-based) -> (its valid sentence numbers, note); None when the reply holds no
    readable list. A passage the reply leaves out is missing from the result."""
    obj = json_object(raw)
    rows = obj.get("passages") if obj else None
    if not isinstance(rows, list):
        return None
    out: dict[int, tuple[list[int], str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        m = re.fullmatch(r"\s*P?(\d+)\s*", str(row.get("id") or ""))
        if not m or not 0 <= int(m.group(1)) - 1 < len(batch):
            continue
        pos = int(m.group(1)) - 1
        n_sent = len(batch[pos]["sentences"])
        nums: list[int] = []
        for x in row.get("sentences") or []:
            try:
                n = int(x)
            except (TypeError, ValueError):
                continue
            if 1 <= n <= n_sent and n not in nums:
                nums.append(n)
        out[pos] = (sorted(nums), " ".join(str(row.get("note") or "").split())[:300])
    return out


def read_batch(call: Call, question: str, batch: list[dict], corpus: str = CORPUS) -> dict:
    """One batch: ``{"results": {key: {"sentences", "note"}}, "failed": [keys], "usage": [...]}``. A
    reply that cannot be read, and any passage it leaves out, is asked again one passage at a time;
    what still fails is reported, never fatal."""
    usage: list[dict] = []

    def ask(ps: list[dict]) -> dict[int, tuple[list[int], str]] | None:
        try:
            text, use = call(read_messages(question, ps, corpus))
        except Exception as exc:  # reported as unread
            print(f"[read] call failed: {type(exc).__name__}: {str(exc)[:160]}", file=sys.stderr)
            return None
        usage.append(use)
        return parse_read(text, ps)

    got = ask(batch) or {}
    results: dict[str, dict] = {}
    failed: list[str] = []
    for pos, p in enumerate(batch):
        if pos not in got and len(batch) > 1:
            again = ask([p])
            if again and 0 in again:
                got[pos] = again[0]
        if pos not in got:
            failed.append(p["key"])
            continue
        nums, note = got[pos]
        results[p["key"]] = {"sentences": nums, "note": note}
    return {"results": results, "failed": failed, "usage": usage}


# ---- the model -------------------------------------------------------------------------------------


def claude_caller(model: str, effort: str, max_tokens: int = MAX_TOKENS, attempts: int = 6) -> Call:
    """``call(messages) -> (text, usage)`` through the Anthropic SDK, streaming, with the system
    prompt marked for caching and ``effort`` sent as ``output_config``; an overload or a rate limit
    is waited out and tried again, up to ``attempts`` times."""
    import anthropic

    client = anthropic.Anthropic(timeout=600.0, max_retries=2)

    def call(messages: list[dict]) -> tuple[str, dict]:
        system = [
            {"type": "text", "text": messages[0]["content"], "cache_control": {"type": "ephemeral"}}
        ]
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages[1:],
        }
        if effort:
            kwargs["output_config"] = {"effort": effort}
        for attempt in range(attempts):
            try:
                with client.messages.stream(**kwargs) as stream:
                    final = stream.get_final_message()
                break
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
                status = getattr(exc, "status_code", None)
                retry = status is None or status == 429 or status >= 500
                if not retry or attempt == attempts - 1:
                    raise
                print(f"[claude] {type(exc).__name__}; retry {attempt + 1}", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        text = "\n".join(b.text for b in final.content if getattr(b, "type", "") == "text")
        u = final.usage
        use = {
            "input_tokens": u.input_tokens,
            "output_tokens": u.output_tokens,
            "cache_write_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
            "cache_read_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
        }
        return text, use

    return call


def cost(use: dict, price_in: float = PRICE_IN, price_out: float = PRICE_OUT) -> float:
    """USD for a usage record: cache writes at 1.25 and cache reads at 0.1 times the input price."""
    return (
        use.get("input_tokens", 0) * price_in
        + use.get("output_tokens", 0) * price_out
        + use.get("cache_write_tokens", 0) * price_in * 1.25
        + use.get("cache_read_tokens", 0) * price_in * 0.1
    ) / 1e6


def add_usage(total: dict, use: dict) -> dict:
    for k in ("input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens"):
        total[k] = total.get(k, 0) + int(use.get(k) or 0)
    total["calls"] = total.get("calls", 0) + 1
    return total


# ---- estimate --------------------------------------------------------------------------------------


def estimate(
    passages: list[dict],
    question: str,
    *,
    batch: int = BATCH,
    workers: int = WORKERS,
    corpus: str = CORPUS,
    price_in: float = PRICE_IN,
    price_out: float = PRICE_OUT,
) -> dict:
    """Tokens, cost and time of reading ``passages``, from the characters each call would send and
    the rates measured on the tested runs; no call is made."""
    calls = math.ceil(len(passages) / batch)
    chars = sum(
        len(m["content"])
        for i in range(0, len(passages), batch)
        for m in read_messages(question, passages[i : i + batch], corpus)
    )
    tokens_in = round(chars / CHARS_PER_TOKEN)
    out_lo, out_hi = (len(passages) * r for r in OUT_PER_PASSAGE)
    return {
        "passages": len(passages),
        "calls": calls,
        "input_tokens": tokens_in,
        "output_tokens": [out_lo, out_hi],
        "cost_usd": [
            round((tokens_in * price_in + o * price_out) / 1e6, 4) for o in (out_lo, out_hi)
        ],
        "minutes": round(calls * SECONDS_PER_CALL / max(1, workers) / 60, 1),
        "workers": workers,
    }


# ---- the read --------------------------------------------------------------------------------------


def done_reads(path: Path) -> tuple[dict[str, dict], dict, int]:
    """What an earlier run of the same read finished: results by key, usage so far, seconds so far."""
    results: dict[str, dict] = {}
    usage: dict = {}
    seconds = 0
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("kind") == "run":
                seconds += int(row.get("wall_s") or 0)
                continue
            results.update(row.get("results") or {})
            for use in row.get("usage") or []:
                add_usage(usage, use)
    return results, usage, seconds


def read_corpus(
    call: Call,
    question: str,
    passages: list[dict],
    out: Path,
    *,
    batch: int = BATCH,
    workers: int = WORKERS,
    corpus: str = CORPUS,
    log_every: float = 60.0,
) -> dict:
    """Read ``passages`` in batches, ``workers`` calls at a time, appending each batch to
    ``out/reads.jsonl``; passages an earlier run finished are skipped. Returns the results by key,
    the keys that failed, the usage and the seconds of this run."""
    out.mkdir(parents=True, exist_ok=True)
    log = out / "reads.jsonl"
    meta = out / "question.txt"
    if meta.is_file() and meta.read_text(encoding="utf-8").strip() != question.strip():
        raise SystemExit(f"{out} holds a read of another question; use a new --out")
    meta.write_text(question.strip() + "\n", encoding="utf-8")
    results, usage, _ = done_reads(log)
    todo = [p for p in passages if p["key"] not in results]
    groups = [todo[i : i + batch] for i in range(0, len(todo), batch)]
    failed: list[str] = []
    lock = threading.Lock()
    t0 = last = time.time()
    run_usage: dict = {}

    def one(g: list[dict]) -> None:
        nonlocal last
        got = read_batch(call, question, g, corpus)
        with lock:
            results.update(got["results"])
            failed.extend(got["failed"])
            for use in got["usage"]:
                add_usage(usage, use)
                add_usage(run_usage, use)
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(got, ensure_ascii=False) + "\n")
            if time.time() - last > log_every:
                last = time.time()
                bearing = sum(1 for r in results.values() if r["sentences"])
                print(
                    f"[read] {len(results)}/{len(passages)} read, {bearing} bear on it, "
                    f"${cost(usage):.2f}, {round(time.time() - t0)} s",
                    flush=True,
                )

    if groups:
        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(groups)))) as ex:
            list(ex.map(one, groups))
    wall = round(time.time() - t0)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "run", "wall_s": wall, "batches": len(groups)}) + "\n")
    return {
        "results": results,
        "failed": sorted(set(failed) - set(results)),
        "usage": usage,
        "run_usage": run_usage,
        "wall_s": wall,
    }


EVIDENCE_COLUMNS = (
    "pmid",
    "chunk",
    "page",
    "citation",
    "title",
    "year",
    "sentence_numbers",
    "sentences",
    "note",
)


def write_outputs(
    out: Path,
    question: str,
    passages: list[dict],
    run: dict,
    manifest: dict[str, dict],
    settings: dict,
) -> dict:
    """``evidence.csv``, ``read_log.csv`` and ``usage.json``; returns the usage summary."""
    results, failed = run["results"], set(run["failed"])
    with (out / "evidence.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(EVIDENCE_COLUMNS)
        for p in passages:
            r = results.get(p["key"])
            if not r or not r["sentences"]:
                continue
            m = manifest.get(p["pmid"], {})
            quotes = " ".join(p["sentences"][n - 1] for n in r["sentences"])
            w.writerow(
                [
                    p["pmid"],
                    p["chunk"],
                    p["page"],
                    m.get("citation") or f"PMID {p['pmid']}",
                    m.get("title", ""),
                    m.get("year", ""),
                    " ".join(map(str, r["sentences"])),
                    quotes,
                    r["note"],
                ]
            )
    with (out / "read_log.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pmid", "chunk", "page", "status"])
        for p in passages:
            r = results.get(p["key"])
            status = (
                "bears"
                if r and r["sentences"]
                else "read"
                if r
                else "failed"
                if p["key"] in failed
                else "not read"
            )
            w.writerow([p["pmid"], p["chunk"], p["page"], status])
    bearing = [k for k in (p["key"] for p in passages) if results.get(k, {}).get("sentences")]
    summary = {
        "question": question,
        **settings,
        "passages": len(passages),
        "read": sum(1 for p in passages if p["key"] in results),
        "failed": len(failed),
        "bearing": len(bearing),
        "papers": len({k.split(":")[0] for k in bearing}),
        "usage": {
            **run["usage"],
            "cost_usd": round(cost(run["usage"], settings["price_in"], settings["price_out"]), 4),
        },
        "this_run": {**run["run_usage"], "wall_s": run["wall_s"]},
    }
    (out / "usage.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    return summary


# ---- the gene table --------------------------------------------------------------------------------

_GENE_RX = re.compile(r"\b[A-Z][A-Z0-9]{1,7}(?:-[A-Z0-9]{1,4})?\b")
# Words written like gene symbols that are not genes in this field, or are far more often not.
NOT_GENES = frozenset(
    """
    DNA RNA THE AND FOR WITH WHAT WHICH ARE WAS NOT PCR MRNA SNP CNV OR IN OF TO IS AS AT BY
    ERG EOG RPE OCT FAF AMD LCA RP CSNB CRD ADRP ARRP XLRP BCVA VA IOP ONL OPL INL IPL GCL RNFL ELM
    EZ IZ ISCEV ETDRS ROP FEVR SNV WES WGS NGS AAV CRISPR MRI CT ICG FA ERM CME MD BEST STGD PDE ISS
    OMIM HGMD ACMG LOF GOF NMD DN AD AR XL WT KO
    """.split()  # noqa: SIM905
)


def hgnc_symbols(path: Path) -> dict[str, str]:
    """Symbol as written -> approved symbol: every approved symbol, and each previous or alias
    symbol that belongs to one approved gene only, is not itself an approved symbol, and has three
    characters or more with a digit among them (HRG4, PRP31, CORD2). Shorter or digit-free aliases
    (MIM, II, S1, BBS) match ordinary text far more often than the gene."""
    approved: set[str] = set()
    other: dict[str, set[str]] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if str(row.get("status") or "Approved") != "Approved":
                continue
            sym = str(row.get("symbol") or "").strip()
            if not sym:
                continue
            approved.add(sym)
            for col in ("alias_symbol", "prev_symbol"):
                for a in str(row.get(col) or "").split("|"):
                    a = a.strip().strip('"')
                    if len(a) >= 3 and any(c.isdigit() for c in a):
                        other.setdefault(a, set()).add(sym)
    out = {s: s for s in approved}
    out.update({a: next(iter(s)) for a, s in other.items() if len(s) == 1 and a not in approved})
    return out


def gene_table(evidence: Path, symbols: dict[str, str]) -> list[dict]:
    """One row per gene named in the sentences that bear on the question: how many passages and
    papers name it, the PMIDs, the names it was written as, and the first sentence that names it."""
    genes: dict[str, dict] = {}
    with Path(evidence).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            text = row.get("sentences") or ""
            for tok in dict.fromkeys(_GENE_RX.findall(text)):
                gene = symbols.get(tok)
                if not gene or tok in NOT_GENES:
                    continue
                g = genes.setdefault(
                    gene,
                    {"gene": gene, "passages": 0, "pmids": {}, "written": set(), "example": ""},
                )
                g["passages"] += 1
                g["pmids"][row["pmid"]] = None
                g["written"].add(tok)
                if not g["example"]:
                    sent = next(
                        (
                            s
                            for s in split_sentences(text)
                            if re.search(rf"\b{re.escape(tok)}\b", s)
                        ),
                        text,
                    )
                    g["example"] = f"PMID {row['pmid']}: {sent[:300]}"
    rows = [
        {
            "gene": g["gene"],
            "papers": len(g["pmids"]),
            "passages": g["passages"],
            "written_as": " ".join(sorted(g["written"])),
            "pmids": " ".join(g["pmids"]),
            "example": g["example"],
        }
        for g in genes.values()
    ]
    return sorted(rows, key=lambda r: (-r["papers"], -r["passages"], r["gene"]))


# ---- command line ----------------------------------------------------------------------------------


def _select(passages: list[dict], args: argparse.Namespace) -> list[dict]:
    if args.keys:
        wanted = {k.strip() for k in Path(args.keys).read_text().split() if k.strip()}
        passages = [p for p in passages if p["key"] in wanted]
    if args.sample:
        passages = random.Random(args.seed).sample(passages, min(args.sample, len(passages)))  # noqa: S311
    return passages


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("estimate", "read"):
        p = sub.add_parser(name)
        p.add_argument(
            "--chunks", type=Path, required=True, help="chunks.jsonl: pmid, chunk, page, text"
        )
        p.add_argument("--question", required=True)
        p.add_argument(
            "--keys", type=Path, help="read only these passages (pmid:chunk, one per line)"
        )
        p.add_argument("--sample", type=int, help="read a random sample of this many passages")
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--batch", type=int, default=BATCH)
        p.add_argument("--workers", type=int, default=WORKERS)
        p.add_argument("--corpus", default=CORPUS, help="how the prompt names the corpus")
        p.add_argument("--price-in", type=float, default=PRICE_IN)
        p.add_argument("--price-out", type=float, default=PRICE_OUT)
    rd = sub.choices["read"]
    rd.add_argument("--out", type=Path, required=True)
    rd.add_argument("--manifest", type=Path, help="CSV with doc_id or pmid, citation, title, year")
    rd.add_argument("--model", default=MODEL)
    rd.add_argument("--effort", default=EFFORT, help="low, medium or high; empty to send none")
    g = sub.add_parser("genes")
    g.add_argument("--evidence", type=Path, required=True)
    g.add_argument("--hgnc", type=Path, required=True, help="HGNC hgnc_complete_set.txt")
    g.add_argument("--out", type=Path, help="default: genes.csv next to the evidence")
    g.add_argument("--check", help="comma-separated genes to look up in the table")
    args = ap.parse_args(argv)

    if args.cmd == "genes":
        rows = gene_table(args.evidence, hgnc_symbols(args.hgnc))
        dest = args.out or args.evidence.with_name("genes.csv")
        with dest.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["gene"])
            w.writeheader()
            w.writerows(rows)
        print(f"{len(rows)} genes -> {dest}")
        if args.check:
            have = {r["gene"]: r for r in rows}
            for gene in (x.strip() for x in args.check.split(",") if x.strip()):
                r = have.get(gene)
                print(
                    f"{gene}: "
                    + (f"{r['papers']} papers, {r['passages']} passages" if r else "absent")
                )
        return 0

    passages = _select(load_passages(args.chunks), args)
    est = estimate(
        passages,
        args.question,
        batch=args.batch,
        workers=args.workers,
        corpus=args.corpus,
        price_in=args.price_in,
        price_out=args.price_out,
    )
    print(json.dumps({"estimate": est}))
    if args.cmd == "estimate":
        return 0
    run = read_corpus(
        claude_caller(args.model, args.effort),
        args.question,
        passages,
        args.out,
        batch=args.batch,
        workers=args.workers,
        corpus=args.corpus,
    )
    settings = {
        "model": args.model,
        "effort": args.effort,
        "batch": args.batch,
        "workers": args.workers,
        "price_in": args.price_in,
        "price_out": args.price_out,
        "estimate": est,
    }
    summary = write_outputs(
        args.out, args.question, passages, run, load_manifest(args.manifest), settings
    )
    print(
        json.dumps(
            {k: summary[k] for k in ("passages", "read", "failed", "bearing", "papers")}
            | {"cost_usd": summary["usage"]["cost_usd"], "wall_s": run["wall_s"]}
        )
    )
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
