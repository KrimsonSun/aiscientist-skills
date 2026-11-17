---
name: read-evidence-with-mcp
description: Search citations, retrieve local corpus passages, answer with PaperQA or curate grounded gene evidence through an already configured literature MCP service. Use when that service and the required corpus/model are available and task coverage, citations and partial results must be tracked; retain current retrieval tools when the MCP service is absent.
license: MIT
metadata:
  category: literature
  version: 0.1.2
  status: community
  tags: mcp, literature
  tested-with: aiscientist-mcp-literature 0.0.4, common 0.0.4; bounded complete-result resources verified by local real MCP protocol tests; final image and website acceptance pending; predecessor has public search, retrieval and cited-answer evidence
  compute: Public search and local retrieval tested; model answer/curation resources depend on the configured deployment
  requires-gpu: 'false'
  scheduler: optional
  requires-network: runtime
  requires-secrets: none
  mcp-server: literature
  mcp-package-version: 0.0.4
  image: "docker://ghcr.io/lijinbio/mcp-literature@sha256:05ab531fb89a886e43af07d9730252c0db81a7b7e52c46b5f81bc457f53460ad"
  cpus: "4"
  mem_gb: "24"
  time_limit: "01:00:00"
---

# Read scientific evidence with the literature MCP service

Discover the registered `literature` service and its actual tools. If it is unavailable, keep
existing literature tools and installed corpus/PDF skills. Do not assume a prefixed MCP tool
exists or replace a working model credential/billing path. This skill pins the upstream `literature-v0.0.4` release image; service registration and trusted
reference/model settings are still supplied by the operator.

## Pick a tool by the evidence needed

| Tool | Evidence and scope |
| --- | --- |
| `literature_search` | Public keyword `query`, `limit`, optional `pubmed_only` and `abstracts`; citation discovery through Europe PMC. |
| `search_corpus` | Local `queries`, `terms`, optional `pmids`, `top_k`, `max_per_paper`; verbatim retrieved passages with citation/page and retrieval diagnostics. |
| `deep_literature` | A `question` answered with the configured PaperQA model and prebuilt corpus index; inspect supporting contexts. |
| `extract_haploinsufficient_genes` | Whole-corpus gene-evidence curation, with retrieval/pilot controls, optional `pmids` and a complete typed `spec` for a different property. |

A retrieval hit is evidence to read, not an automatic answer. A top-k search does not establish
whole-corpus completeness. For extraction, retain the `spec` definition, inclusion/exclusion
rules and requests. A positive `max_passages` is a smoke-test cap and must be reported as partial.
Use pilot diagnostics before scaling an expensive curation job.

## Bind the deployed corpus and model

The operator supplies `LITERATURE_CORPUS_ROOT`, admitted roots, PDF/manifest/text/vector paths,
staged PubMedBERT weights and the PaperQA index. Shared corpus assets stay read-only. Queries
may create derived caches only inside the analysis. Do not silently change corpus versions
or model identity while resuming judgments; start a new `analysis_id` for those changes.

`search_corpus` does not call a generative model. Answering and extraction require explicit
server-side model settings; absent settings are a deployment failure, not permission to invent
an answer. Public search sends its keywords to Europe PMC, and PaperQA can request bibliographic
metadata. Keep clinical identifiers out of a public search unless that transmission is intended.
A configured model receives the evidence required by its operation. Standalone deployments use
OpenAI-compatible endpoints. AiScientist can bind the selected session model through its guarded
gateway relay, including native Anthropic: provider credentials stay on the gateway and each call
keeps its usage/budget checks. Credentials are never tool arguments. Claude uses supported provider
sampling defaults and low effort when a worker requests thinking off; do not claim temperature-zero
or identical model answers across providers.

The AiScientist relay reports actual priced usage to extraction's pilot and spending checks.
With a positive `max_cost_usd`, inspect the pilot's projected total before a full scan. Further
calls stop after the cap is reached; one already running provider call may cross it. Missing
accounting stops further calls. A standalone endpoint without this explicit usage protocol
refuses a positive dollar cap; use its deployment's spending controls.

## Finish and validate

All action tools accept `analysis_id` and `rerun`. Poll
`literature_job_status(analysis_id, task_id)` to `COMPLETED` after asynchronous submission;
inline waits in the current allocation. Keep task IDs and failures. A failed or empty evidence
step does not count as a supported finding.

Inspect citation identifiers, actual passages, quote verification, HGNC resolution, coverage,
review flags and unread/pilot diagnostics. Where the response is bounded, `full_result` and
artifact tables contain the complete data; total counts are not the preview length. Distinguish
no retrieved evidence from evidence that contradicts a claim. Report corpus/model versions,
method, limits, task IDs and only citations that support the associated statement.

For a completed large result, `full_result_uri` identifies bounded MCP `resources/read`
pages. Read every page and verify the task identity, contiguous offsets, stable total size and
SHA-256 before treating the JSON as complete evidence. The service refuses results over 32 MiB.
The 0.0.4 resource repair has local real-protocol tests for large synthetic evidence and missing
or corrupt pages; its final released-image and selected-session website gates remain pending.

Predecessor native-image acceptance includes Europe PMC, RetiGene/PubMedBERT retrieval and a cited answer
to a public PRPF31 deletion/segregation question. A broader mechanism question abstained despite
retrieved contexts. The four-passage extraction smoke produced a flagged gene candidate, not a
validated gene list or whole-corpus curation. Verify the actual answer and review flags for
each new question; successful execution alone does not establish scientific support.
