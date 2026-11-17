---
name: rank-phenotype-differentials-with-mcp
description: Map clinical phenotype text to grounded HPO terms and rank a research differential through an already configured phenotype-diagnosis MCP service with LIRICAL and optional literature adjudication. Use for explicit service-based analysis while preserving negation, uncertainty and original probabilities; retain the established workflow when the service is unavailable.
license: MIT
metadata:
  category: variants
  version: 0.1.2
  status: community
  tags: mcp, phenotype-diagnosis
  tested-with: aiscientist-mcp-phenotype-diagnosis 0.0.4, common 0.0.4; complete literature evidence verified by local real MCP protocol tests; final image and website acceptance pending; predecessor has synthetic HPO/LIRICAL evidence
  compute: 'Real staged LIRICAL phenotype-only check: 8621 candidates; input was synthetic, not patient data'
  requires-gpu: 'false'
  scheduler: optional
  requires-network: runtime
  requires-secrets: none
  mcp-server: phenotype-diagnosis
  mcp-package-version: 0.0.4
  image: "docker://ghcr.io/lijinbio/mcp-phenotype-diagnosis@sha256:d20ed2dc2e576b8a524946d13816757ecb0a7b72da0299b7f022e4f89f351f21"
  cpus: "4"
  mem_gb: "24"
  time_limit: "01:00:00"
---

# Rank a phenotype differential through MCP

Use the already registered `phenotype-diagnosis` service, discovering the host's actual tool
names and schemas. Without it, retain the existing phenotype tools. Do not create prefixed
aliases, replace the configured model/billing path, or treat this new community skill as a
production image registration. It contains no diagnostic model or reference data.

## Ground the phenotype representation

Call `map_phenotype_to_hpo(text, k)` with a stable `analysis_id`. Inspect each observed and
excluded term, label, supporting phrase, ontology version, unmapped phrase and warning.
Do not turn family history, hypothetical findings, or negation into observed patient features.

Standalone model extraction requires an operator-configured OpenAI-compatible endpoint.
AiScientist can bind its selected session model, including native Anthropic, through the guarded
gateway relay with per-call usage and budget checks. Provider credentials stay on the gateway.
The conservative lexical fallback
can return `mode="needs_llm"` for negation/family-history text with no asserted terms. That
means the mapping is unresolved, not that the person has no phenotype. Correct the inputs
from evidence before proceeding; do not fill in missing terms from prior expectations.

## Rank with the configured evidence

`run_lirical` accepts `hpo_terms`, optional `excluded_hpo`, `sample_id` and admitted `vcf_path`.
`diagnose_disease` adds `candidate_genes` and `max_literature_queries`. All actions accept
`analysis_id` and `rerun`. A VCF is explicitly supplied; this service does not guess a bound
app dataset. The operator sets `PHENOTYPE_ALLOWED_ROOTS`, the LIRICAL command/data, assembly,
and matching Exomiser references. Without both a VCF and the matching genotype data, label a
ranking phenotype-only rather than genotype-supported.

The optional literature service is separately configured by `PHENOTYPE_LITERATURE_COMMAND`.
No configured literature endpoint means LIRICAL-only evidence, not a completed literature
review. Phenotype phrases can enter literature questions and model prompts; use the intended
configured services and the application's trusted credential path. Credentials and commands
are never model-controlled tool arguments.

## Poll, inspect and report uncertainty

Retain `analysis_id`, `task_id`, and Slurm `job_id` where present. Poll `phenotype_job_status`
until `COMPLETED`; a failed mapping/ranking must remain a failure in the report. Each LIRICAL
attempt has a unique TSV so a failed attempt cannot reuse a stale ranking. Inline execution
waits in the existing allocation.

Read the original LIRICAL probabilities and scoring mode, complete TSV/full result, mapped and
excluded HPO terms, evidence grades, citations and flags. Literature adjudication must not
replace the original LIRICAL probability with a model's confidence. No retrieved evidence is
not the same as refutation. If the literature service returns `response_omitted=true`, version
0.0.4 reads its bounded MCP result-resource pages and verifies task identity, size, contiguous
offsets and SHA-256 before scoring the complete evidence. Missing, oversized or inconsistent
pages remain an explicit ungraded failure; a preview alone is never complete evidence.
Bounded previews retain total counts; consult `full_result` before
claiming to have reviewed every candidate. Present a research differential and uncertainties,
not an established diagnosis.

Real staged LIRICAL was exercised with synthetic clinical input and returned 8,621 candidate
rows; complete results, bounded MCP previews and status calls were checked. This is not a
patient validation or validation of the generative extraction/literature path. Track those
separate deployment gates before removing the current application workflow.

The predecessor's selected-session website test completed HPO mapping and LIRICAL, but its
truncated literature reply could not be graded. Version 0.0.4 repairs that protocol gap and has
real stdio tests using large synthetic evidence. Final released-image and website model
acceptance remain pending; do not describe that earlier LIRICAL-only result as completed
literature adjudication.
