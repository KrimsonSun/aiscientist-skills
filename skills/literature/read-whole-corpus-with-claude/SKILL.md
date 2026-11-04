---
name: read-whole-corpus-with-claude
description: Answer a question from a chunked full-text literature corpus completely, by having Claude Haiku read every passage (not the top-k of a search) and return the numbers of the sentences that bear on it, so every quote is verbatim. Writes evidence.csv (each bearing passage with its sentences, PMID, page and citation), a read log, measured tokens and cost, and for a gene-list question a table of every HGNC gene those sentences name. Tested on the RetiGene corpus of inherited retinal disease papers (39,563 passages). Use when a question needs every paper that reports something (every gene with a property, every study of a variant or phenotype), when a RAG or PaperQA answer built from the best 10-30 chunks may be incomplete, to check how complete such an answer is, or to estimate the cost and time of reading a corpus before running it. Not for a quick lookup of one fact.
license: MIT
compatibility: Python 3.11 or newer with the anthropic package, an Anthropic API key with room for about 50 concurrent requests, and the corpus as chunks.jsonl (pmid, chunk, page, text); optionally its manifest CSV and the HGNC complete set. No GPU, no scheduler.
metadata:
  category: literature
  version: "0.0.1"
  status: community
  author: "Yijun Sun"
  tags: "literature, rag, corpus, full-text, evidence, claude, haploinsufficiency, retina"
  tested-with: "anthropic 1.13.0 (Python SDK), claude-haiku-5-5 at effort medium, Python 3.13.3"
  compute: "whole RetiGene corpus (39,563 passages, one question): 4,012 calls, 408 s with 48 parallel calls, $5.31 (Claude Haiku 5.5 at $0.10 / $0.50 per million input / output tokens); a 3,270-passage sample: 327 calls, 42 s, $0.47; estimate and gene table: seconds on one CPU"
  requires-gpu: "false"
  scheduler: "none"
  requires-network: "runtime"
  requires-secrets: "ANTHROPIC_API_KEY"
---

# Read a whole corpus with Claude

`scripts/read_corpus.py` sends every passage of a corpus to Claude Haiku, ten per call, each split
into numbered sentences, with one question. For each passage Claude returns the numbers of the
sentences that bear on the question and a short note. The script takes those sentences from the
text by number, so no quote can be invented, and writes them to `evidence.csv`.

Why read everything: an answer spread over hundreds of papers is mostly in passages that do not
look like the question. On the RetiGene corpus (measured in AiScientist's benchmark):

- a top-12 hybrid search found 103 of 184 graded answering passages on 32 questions;
- a focused read (every passage naming the subject, then the nearest ones) found 181 of them, but
  only 51-59% of what a whole read found on two broad questions;
- ranked by chunk embeddings, a one-topic question needed the first 16,088 passages to cover all its
  answering passages, and a gene-list question needed 32,214 of 39,563 for 99%.

The thing most likely to go wrong is the last step, not the read: a prose answer written from the
evidence of a list question dropped 20 of the 51 genes that evidence named. For a list, report the
table, not a summary.

Tested on the RetiGene corpus: 1,736 full-text papers on inherited retinal disease, 39,563
passages (`chunks.jsonl`, 69 MB), with the question "Which genes cause inherited retinal disease
through haploinsufficiency?":

| Run | Passages | Calls | Time | Cost | Bearing | Graded answering passages found |
| --- | --- | --- | --- | --- | --- | --- |
| sample: the 270 graded passages + 3,000 at random | 3,270 | 327 | 42 s | $0.47 | 492 | 253 of 270 (93.7%) |
| whole corpus | 39,563 | 4,012 | 408 s | $5.31 | 3,780 (1,109 papers) | 259 of 270 (95.9%) |

"Graded" passages are the ones Claude Haiku rated as answering the question (2 on a 0-2 scale) when
it graded every passage an earlier whole read had marked. The same prompt and settings, run from
AiScientist's own code, found 94.7% (sample) and 97.4% (whole corpus, $5.32, 404 s) of the
passages graded at the time: one reading is not perfectly repeatable.

Replace every `/path/to/...` with your own paths.

## When to use

- A question whose answer is a set: every gene with a property, every paper that reports an
  outcome, every variant seen with a phenotype.
- Checking how complete a RAG answer is: read the corpus once and compare.
- Costing a read before running it (`estimate` makes no call).

## When NOT to use

- One fact from one or two papers: a search is enough and costs nothing.
- A corpus you have no right to send to an API provider: every passage goes to Anthropic.
- A question you cannot state without ambiguity: each passage is judged against the question as
  written, so settle what counts first (see §5).

## 1. Environment setup

```bash
python3.13 -m venv /path/to/envs/read_corpus
/path/to/envs/read_corpus/bin/pip install anthropic==1.13.0
/path/to/envs/read_corpus/bin/python scripts/read_corpus.py read --help
export ANTHROPIC_API_KEY=...            # or ANTHROPIC_BASE_URL and a token for a proxy
```

The script uses only the standard library and `anthropic`. The tests run without either a key or
the package: `python -m pytest tests` (12 tests, about a second).

## 2. Prepare inputs

| File | Needed by | Format |
| --- | --- | --- |
| `chunks.jsonl` | `estimate`, `read` | one passage per line: `{"pmid": "1302020", "chunk": 0, "page": 1, "text": "..."}` |
| `manifest.csv` | `read`, optional | `doc_id` (or `pmid`), `citation`, `title`, `year`: puts the citation in `evidence.csv` |
| `hgnc_complete_set.txt` | `genes` | the HGNC complete set (tab-separated, `symbol`, `alias_symbol`, `prev_symbol`, `status`), from <https://www.genenames.org/download/> |

A passage is keyed `pmid:chunk`; passages without text and repeated keys are skipped. Any chunked
corpus in this shape works. AiScientist's literature index writes it as
`mechanism_cache/chunks.jsonl`, with `manifest.csv` and `hgnc_complete_set.txt` beside it.

## 3. Configure

The defaults are the tested settings. Change them only for the reasons given.

| Option | Default | Why |
| --- | --- | --- |
| `--model` | `claude-haiku-5-5` | the model the method was measured with; Claude Sonnet 5.5 costs 20 times more per token |
| `--effort` | `medium` | `low` saved 8-18% of the cost but found 87% of the graded passages on the gene-list sample, against 95% |
| `--batch` | `10` | passages per call. A yes/no screen of 30 or 50 passages per call before the read saved about 40% and lost 21-43% of the answering passages |
| `--workers` | `48` | parallel calls. 48 ran with no rate-limit retries on the tested key; lower it if `[claude] RateLimitError` lines appear |
| `--corpus` | `the lab's RetiGene corpus (inherited retinal disease)` | how the prompt names the corpus; describe your own. Any other text is a prompt change the results above do not cover |
| `--price-in`, `--price-out` | `0.10`, `0.50` | USD per million tokens, for `usage.json` and the estimate |

## 4. Run

```bash
C=/path/to/corpus/mechanism_cache/chunks.jsonl
Q="Which genes cause inherited retinal disease through haploinsufficiency?"

# 1. What it will cost (no call is made).
python scripts/read_corpus.py estimate --chunks "$C" --question "$Q"

# 2. A small read first: check the evidence makes sense before paying for the whole corpus.
python scripts/read_corpus.py read --chunks "$C" --question "$Q" --sample 500 --out /path/to/out/sample

# 3. The whole corpus.
python scripts/read_corpus.py read --chunks "$C" --question "$Q" \
  --manifest /path/to/corpus/manifest.csv --out /path/to/out/whole

# 4. For a gene-list question: every gene the evidence names.
python scripts/read_corpus.py genes --evidence /path/to/out/whole/evidence.csv \
  --hgnc /path/to/corpus/hgnc_complete_set.txt --check PRPF31,PAX6,OTX2
```

What the tested whole read printed for steps 1 and 3:

```text
{"estimate": {"passages": 39563, "calls": 3957, "input_tokens": 31735847, "output_tokens": [2888099, 4312367], "cost_usd": [4.6176, 5.3298], "minutes": 6.6, "workers": 48}}
{"passages": 39563, "read": 39563, "failed": 0, "bearing": 3780, "papers": 1109, "cost_usd": 5.3148, "wall_s": 408}
```

`estimate` counts the characters each call would send and converts them with the rates of the
tested runs (2.3 characters per input token; 73-109 output tokens per passage; 4.8 s per call per
worker). On the RetiGene corpus it gives $4.61-5.33 and 6.6 minutes; the two measured whole reads
cost $4.61 and $5.32.

`read` appends every finished batch to `<out>/reads.jsonl`. If a run stops, or exits with status 1
because some passages could not be read, run the same command again: it reads only what is
missing. A folder holds one question; the script refuses another one there.

## 5. Validate before using the output

| File | Contents |
| --- | --- |
| `evidence.csv` | one row per passage that bears on the question: `pmid`, `chunk`, `page`, `citation`, `title`, `year`, `sentence_numbers`, `sentences` (verbatim), `note` |
| `read_log.csv` | every passage: `bears`, `read`, `failed` or `not read` |
| `usage.json` | the question, settings, estimate, passages read and failed, bearing passages and papers, tokens, cost and time |
| `reads.jsonl` | every batch as it finished (the resume record) |
| `genes.csv` | from `genes`: `gene`, `papers`, `passages`, `written_as`, `pmids`, `example` |

Check these, in this order:

1. **Coverage** (`usage.json`): `read` equals `passages` and `failed` is 0. Re-run until it is.
2. **Cost** against the estimate. Far more output tokens per passage than 109 means the model is
   writing more than it was asked; check a few replies in `reads.jsonl`.
3. **The evidence makes sense.** Read 20 rows of `evidence.csv`. Almost none bearing, or thousands
   that only mention the subject, means the question or `--corpus` misleads the reader.
4. **Known answers are there.** For the tested question, `genes --check` with the lab's 24
   reference genes found 23. The missing one, GATAD2B, has one reference passage, from a paper on
   an intellectual-disability syndrome; the read judged that paper not to be about retinal disease.
   A known answer that is missing points to a passage the read did not take as bearing: look it up
   in `read_log.csv` and in its batch in `reads.jsonl`, which holds the note on every passage.
5. **Decide what counts before judging candidates.** The read is inclusive: for the tested question
   it marked many passages that state a heterozygous loss-of-function cause without the word
   haploinsufficiency (BMP4, OTX2, PAX6), which the lab counts, and also passages that are only
   related (a gene's dominant inheritance, a carrier's milder sign). `genes.csv` is therefore a
   candidate table, ranked by papers: every approved symbol, or digit-bearing alias of exactly one
   gene (HRG4, PRP31, CORD2), written in a bearing sentence. For the tested question it held 849
   genes, 338 of them named in two or more papers, and the 24 reference genes ranked from 1st (CRX)
   to 416th (SHH). The paper count is not a verdict: judge each candidate from its quotes in
   `evidence.csv`, not from memory.

## Writing the answer

- Answer from `evidence.csv` only, citing PMIDs. Never add a paper or a gene the evidence does not
  hold.
- For a list question, give the full candidate table with each gene's papers and an example quote,
  and mark which candidates the quotes support. Don't shorten it into prose.
- When the evidence does not fit one context, group the rows by paper, write notes per group with
  the PMIDs of every paper that reports each finding, and answer from the notes.

## Report

Include:

- the question, exactly as it was read;
- the corpus (file, passages, papers) and the model, effort, batch and workers;
- passages read and failed, bearing passages and papers, tokens, cost and time (`usage.json`);
- `evidence.csv`, and for a list question `genes.csv` with the judgement of each candidate;
- the caveats: one reading by one model (93.7-97.4% of the graded passages in the tested runs), the
  table is candidates, and every passage was sent to the API provider.

Keep "the whole corpus was read" separate from "the answer is complete".
