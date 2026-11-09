---
name: query-retigene-papers-with-aiscientist-mcp
description: Answer a question about the RetiGene papers (about 1,700 full-text papers on inherited retinal disease), such as "What are haploinsufficient genes in RetiGene papers?", by calling the retigene-rag MCP server from the aiscientist-mcp repository. Its tools search every sentence by keyword and the passages by chunk embedding, and run a corpus-wide curation that grades each gene from its own sentences (A stated, B hedged or contested, N not supported) into a gene table and a sentence table, each row with a verbatim quote, PMID and page. Use when asked which genes in the RetiGene papers have a property (haploinsufficiency, loss of one copy), what these papers say about a gene, disease or method, or to install or register this server. For another corpus without the server, use read-whole-corpus-with-claude.
license: MIT
compatibility: Requires the aiscientist-mcp packages (common, retigene-rag) from GitHub or apptainer with the pinned server image, a copy of the RetiGene index (the AiScientist shared dataset retigene, about 440 MB), an MCP client (Claude Code or any stdio MCP client) or the bundled aiscientist-mcp CLI client, and a model, a Claude API key or an OpenAI-compatible endpoint such as a vLLM server. No GPU on the server side. Network for the model calls.
metadata:
  category: literature
  version: "0.0.1"
  status: community
  author: "Yijun Sun"
  tags: "literature, rag, mcp, retina, inherited-retinal-disease, haploinsufficiency, gene-curation, claude"
  tested-with: "aiscientist-mcp common 0.0.2 and retigene-rag 0.0.1 (pip, and the image of containers/retigene-rag), mcp 2.3.0, anthropic 1.13.0, Python 3.13.3, Claude Haiku 5.5 and Claude Sonnet 5.5, Claude Code 2.1.205; the RetiGene index of 2026-10-11 (1,736 papers, 426,706 sentences)"
  compute: "one curation: 2.5-3.5 min, 711-770 model calls, 2.2-2.4 M input and 0.45-0.49 M output tokens, $0.31-0.39 with Claude Haiku reading and reviewing ($0.78 with a Claude Sonnet review); asked again it is reused at once, and with rerun it takes 17 s from the reply cache; other calls 2-15 s each as one-shot CLI or container calls, most of it loading the corpus (about 2 GB of memory); no GPU"
  image: "docker://ghcr.io/lijinbio/mcp-retigene-rag@sha256:DIGEST"
  cpus: "2"
  mem_gb: "8"
  time_limit: "01:00:00"
  requires-gpu: "false"
  scheduler: "none"
  requires-network: "runtime"
  requires-secrets: "ANTHROPIC_API_KEY"
---

# Query the RetiGene papers with the retigene-rag MCP server

The [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp) server `retigene-rag` exposes the
RetiGene corpus as MCP tools. This skill holds no code: every step is a tool call.

- In an MCP client such as Claude Code, call the tools directly.
- In a shell or batch script, use the bundled client:
  `aiscientist-mcp --server retigene-rag-mcp call <tool> '<json>'`.

The index is the AiScientist shared dataset `retigene`: 1,736 papers with text, 39,563 passages, 426,706
sentences, the passages' PubMedBERT vectors, the paper manifest and the HGNC table. It is only read, never
written. Replace every `/path/to/...` with your own values.

## When to use

- "Which genes in the RetiGene papers are haploinsufficient?" or another list of every gene with a
  dosage property: the curation reads every sentence that states it, not the top-k passages.
- "What do the RetiGene papers say about PRPF31 / Coats disease / AAV dosing?": search by meaning or by
  exact words, then read the passages.
- Installing, registering or troubleshooting the `retigene-rag` server.

## When NOT to use

- Another corpus, or no server: `read-whole-corpus-with-claude` reads a `chunks.jsonl` directly.
- Evidence outside these papers (ClinGen, OMIM, PubMed at large): the grades use the corpus text only.
- A property other than haploinsufficiency for the curation: its rules are written for that one. Use
  `search_sentences` and `read_passage` for others.

## 1. Install the server

The install is pinned to release tags of `lijinbio/aiscientist-mcp`: `common-v0.0.2` and
`retigene-rag-v0.0.1`.

```bash
python3.13 -m venv /path/to/envs/retigene-mcp
source /path/to/envs/retigene-mcp/bin/activate
pip install mcp==2.3.0 anthropic==1.13.0 numpy
for t in common-v0.0.2 retigene-rag-v0.0.1; do
  pip install --no-deps --force-reinstall "git+https://github.com/lijinbio/aiscientist-mcp@${t}#subdirectory=packages/${t%-v*}"
done
aiscientist-mcp --server retigene-rag-mcp tools   # lists the 10 tools below
```

`search_passages` also needs the embedding stack, CPU only:
`pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 && pip install sentence-transformers==6.2.0`.
The curation and the other tools do not.

**Container.** The image holds the server, the embedding stack and the query model at the revision that made
the index's vectors (its vectors for stored passages equal the stored ones, cosine 1.000000). It was tested
one container per call, with the index mounted read-only and `AISCI_EXECUTOR=inline`:

```bash
docker run --rm -e AISCI_EXECUTOR=inline -e AISCI_DATA_DIR=/work/data -e RETIGENE_INDEX=/index \
  -e ANTHROPIC_API_KEY -v /path/to/datasets/retigene/v2026.11:/index:ro -v /path/to/work:/work \
  ghcr.io/lijinbio/mcp-retigene-rag@sha256:DIGEST aiscientist-mcp --server retigene-rag-mcp tools
```

With apptainer, pull the same digest (`apptainer pull mcp-retigene-rag_0.0.1.sif docker://...`), pass the
settings as `APPTAINERENV_<name>` and bind the index and the data folder.

## 2. Configure

| Variable | Meaning | Tested value |
| --- | --- | --- |
| `RETIGENE_INDEX` | a version of the shared dataset `retigene` | `/path/to/datasets/retigene/v2026.11` |
| `AISCI_DATA_DIR` | data root; curations go to `<root>/retigene-rag/<curation_id>/` | `/path/to/data/aiscientist-mcp` |
| `AISCI_EXECUTOR` | `inline` (the call returns when the curation ends), `local` (background, for a persistent server) or `slurm` | `inline` |
| `ANTHROPIC_API_KEY` | the Claude key (`ANTHROPIC_BASE_URL` for a proxy) | your key |
| `RETIGENE_CHECK_MODEL`, `RETIGENE_REVIEW_MODEL` | the two readers | `claude-haiku-5-5`, `claude-haiku-5-5` |
| `RETIGENE_PROVIDER`, `RETIGENE_BASE_URL`, `RETIGENE_API_KEY` | `openai` and an OpenAI-compatible endpoint instead of Claude | unset (Claude) |
| `RETIGENE_CACHE` | model replies, reused by later curations | `<root>/retigene-rag/cache` |

## 3. Register the server

**Claude Code.** The key is read from your environment when the server starts (`${ANTHROPIC_API_KEY}`),
so `.mcp.json` holds no secret:

```bash
claude mcp add-json --scope project retigene-rag '{"type":"stdio","command":"/path/to/envs/retigene-mcp/bin/retigene-rag-mcp","env":{"RETIGENE_INDEX":"/path/to/datasets/retigene/v2026.11","AISCI_DATA_DIR":"/path/to/data/aiscientist-mcp","AISCI_EXECUTOR":"local","ANTHROPIC_API_KEY":"${ANTHROPIC_API_KEY}"},"timeout":900000}'
claude mcp get retigene-rag   # project scope: "Pending approval" until you run `claude` and approve
```

`AISCI_EXECUTOR=local` lets `submit_curation` return at once in a persistent session; poll `curation_status`.
**Other MCP clients:** put the same object under `"mcpServers": {"retigene-rag": {...}}`.

## 4. Tools

| Tool | Arguments | Returns | Time (tested) |
| --- | --- | --- | --- |
| `search_sentences` | `terms`, `gene`, `limit`, `offset` | every sentence holding a term, as `PMID p c: sentence` lines, with the total | 10 s |
| `search_passages` | `query`, `terms`, `top_k` | the passages nearest the query by embedding; with `terms`, only passages holding them | 15 s |
| `read_passage` | `pmid`, `chunk` | the passage with citation, title and DOI | seconds |
| `submit_curation` | `question`, `terms`, `estimate_only`, `max_cost_usd`, `rerun` | `curation_id`, `state`, the A and B genes, time, calls, tokens, cost | 2.5-3.5 min; estimate 19 s |
| `curation_status` | `curation_id` | `state`, model calls so far | seconds |
| `get_genes` | `curation_id`, `grades`, `top`, `full` | the gene table | seconds |
| `get_evidence` | `curation_id`, `gene`, `pmid`, `grades`, `offset`, `limit` | the sentence table | seconds |
| `evaluate` | `curation_id`, `reference` | A recall (all, 10 ocular, 5 syndromic), B apart, N listed, against the curator reference of 2026-11-04 | seconds |
| `write_report` | `curation_id` | `report.md` with both tables | seconds |
| `list_curations` | none | `curations` | seconds |

## 5. Ask the haploinsufficiency question

These are the calls of the tested run, in order. In Claude Code they are the tools
`mcp__retigene-rag__search_sentences`, `..._submit_curation`, and so on, with the same JSON arguments.

```bash
S="aiscientist-mcp --server retigene-rag-mcp"
Q="What are haploinsufficient genes in RetiGene papers?"

# 1. What the corpus says (tested: 396 sentences hold "haploinsufficien").
$S call search_sentences '{"terms": ["haploinsufficien"], "limit": 3}'

# 2. What the curation would cost, with no model call (tested: 301 genes, $0.25-0.40, 678-753 calls).
$S call submit_curation "{\"question\": \"$Q\", \"terms\": [\"haploinsufficien\"], \"estimate_only\": true}"

# 3. The curation; note the curation_id (tested: 156 s, 712 calls, $0.31 with Claude Haiku).
$S call submit_curation "{\"question\": \"$Q\", \"terms\": [\"haploinsufficien\"]}"

# 4. The tables, the score and the report (seconds each).
ID=haploinsufficiency-<id from step 3>
$S call get_genes "{\"curation_id\": \"$ID\", \"grades\": \"A,B\"}"
$S call get_evidence "{\"curation_id\": \"$ID\", \"gene\": \"PRPF31\", \"limit\": 3}"
$S call evaluate "{\"curation_id\": \"$ID\"}"
$S call write_report "{\"curation_id\": \"$ID\"}"
```

An agent given only the server's tools does the same by itself: in all eight tested agent runs (Claude Haiku
and Claude Sonnet, the question above and "Which genes cause eye disease when one copy is lost, according to
the RetiGene papers?") it searched "haploinsufficien" with variants of its own and called `submit_curation`
once. Words for the same property ("one copy", "reduced dosage") may be added; the curation always reads
the rules' own dosage wording too.

For a question about one topic:

```bash
$S call search_passages '{"query": "PRPF31 haploinsufficiency retinitis pigmentosa", "top_k": 3}'
$S call read_passage '{"pmid": "24419317", "chunk": 0}'
```

## 6. Validate before using the output

Each curation folder `$AISCI_DATA_DIR/retigene-rag/<curation_id>/` holds `genes.csv` (one row per gene),
`sentences.csv` (one row per sentence read, with its checks), `requests.csv` (what each term found),
`curation.json` (models, terms, time, calls, tokens, cost) and `report.md`. Check, in this order:

1. **Coverage** (`found` in the result): sentences and genes found. A term that finds nothing, or far fewer
   sentences than `search_sentences` showed, means a typo.
2. **Grades**: every A row has a `quote` copied verbatim from the corpus, with its `pmid`, `page` and
   `sentence_id`; `code_adjusted` says where the rules changed the review model's grade, and why.
3. **Unresolved genes** (`unresolved`): genes whose replies could not be read are listed apart and never as
   A. `submit_curation` with `rerun=true` reads them again, the others from the cache.
4. **Against the reference** (`evaluate`): on the haploinsufficiency question every tested run listed the 15 A genes as A (10/10 ocular, 5/5 syndromic), kept the 7 B genes apart and listed neither N gene. A genes outside the reference (ABCA4, FSCN2 every run; CLN8, FH in some) are for a curator to check: FH is factor H, the CFH protein, read as a gene.

## Report

Include the question, the terms, the index version (`index` in the result), the two models, the A genes and
the B genes apart, each with quote, PMID and page, the run's time, model calls, tokens and cost, and the
caveat that the grades come from the corpus text alone (FZD4 and SOX2 are B on this corpus, though ClinGen
scores them 3).
