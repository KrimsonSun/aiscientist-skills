# Changelog

All notable changes to this repository are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the registry uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `literature/read-whole-corpus-with-claude` 0.0.1: answers a question from a chunked full-text
  corpus by having Claude Haiku read every passage, ten per call, as numbered sentences, and keep
  the sentences that bear on it (verbatim, with PMID and page). `scripts/read_corpus.py` estimates
  the cost before a read, resumes a read that stopped, and builds a table of every HGNC gene the
  evidence names for a gene-list question. Tested on the RetiGene corpus (39,563 passages). It
  comes with the trigger eval `list-every-gene-from-paper-corpus`.

- `literature/query-retigene-papers-with-aiscientist-mcp` 0.0.1: answers a question about the
  RetiGene papers, such as "What are haploinsufficient genes in RetiGene papers?", by calling the
  `retigene-rag` MCP server of [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp): keyword
  search over every sentence, embedding search over passages, and a corpus-wide curation that grades
  each gene from its own sentences into a gene table and a sentence table with verbatim quotes, PMIDs
  and pages. Only install, registration and tool calls, with tested times and costs: in ten runs it
  listed the curator's 15 A genes as A, kept the 7 B genes apart and listed neither N gene, at
  $0.31-0.39 and 2.5-3.5 min per question with Claude Haiku. It comes with the trigger eval
  `list-haploinsufficient-genes-in-retigene`.

## [0.2.0] - 2026-11-04

### Added

- `single-cell/explore-atlas-expression-with-aiscientist-mcp` 0.0.1: answers a query such as "show
  LRAT across retinal cell types" on a large atlas `.h5ad` by calling the
  `atlas-expression-exploration` MCP server of
  [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp). It covers gene-name resolution,
  the full-atlas scanpy step on a big-memory Slurm node, donor-aware tables, scanpy dot, violin and
  UMAP plots, and a report. The skill holds only install, registration and tool-call commands, and
  pins release tags and the server image digest. Tested on the HRCA snRNA-seq atlas (3.18M nuclei).
  It comes with the trigger eval `show-gene-across-retina-cell-types`.

## [0.1.0] - 2026-10-23

### Changed

- Releases ship three assets instead of one zip per skill: `aiscientist-skills-<version>.zip`, with
  every skill folder at its catalog `path`, plus `catalog.json` and `SHA256SUMS`.
  `aiscientist-skill package --per-skill` still builds one zip per skill, for the Claude apps.
- `single-cell/qc-snrna-with-cellqc-standalone` 1.2.0: ships its reference settings in
  `assets/cellqc-defaults.json` (gene sets per reference, the expected doublet rate per chemistry
  with the reaction capacity, and the default count filters), which AiScientist's `run_cellqc`
  reads instead of keeping a copy (RCHENLAB/AiScientist#42). The Configure step points to it.
- `variants/normalize-vcf-with-bcftools`: the `bcftools norm` pipeline shell-quotes its paths,
  runs under `bash -c` instead of a login shell, and sets `pipefail` with every stage's stderr
  kept, so a failure in any stage is reported (review of #7).
- `single-cell/qc-snrna-with-cellqc-standalone`: the description now says that inside AiScientist
  the `run_cellqc` tool runs this skill's pipeline, instead of "not this skill", matching the body
  and the plan for AiScientist to load its skills from this registry.
- `CONTRIBUTING.md` documents the `metadata` keys AiScientist reads: `aliases`, `image`, `cpus`,
  `mem_gb` and `time_limit`.

- `single-cell/qc-snrna-with-cellqc-standalone` 1.1.0: Python pinned to `>=3.12,<3.14` in the
  install command, a container route (a pinned apptainer image built without root), when to use
  it and when not, and how it runs inside AiScientist (`image`, `cpus`, `mem_gb`, `time_limit` in
  `metadata`, read by AiScientist's `run_in_environment`). The `r-doubletfinder` note says that
  bioconda `cellqc` 0.3.6 depends on it from build 1.
- The `aiscientist-skill` tooling no longer assumes uv. It installs with `pip install -e '.[dev]'`,
  pipx, uv or conda, the docs show the bare command, the pre-commit hook runs whatever
  `aiscientist-skill` is on `PATH`, and CI adds an "Install with pip" job. `uv.lock` remains the
  pin for CI's own dependency versions.
- Docs show how to install the CLI straight from GitHub (`pip install git+https://…`, pipx,
  `uvx --from`), pinned to a release tag.
- Test matrix now covers Python 3.11 and 3.14; the package declares support through 3.14.
- Registry framing: skills for scientific data analysis, with computational biology as the first
  category.

### Added

- Skills migrated from AiScientist's own `skills/` folder (RCHENLAB/AiScientist issue 30), each
  1.0.0 and `community`, with `scripts/reference.py`, pytest tests on synthetic data (skipped where
  the scientific packages are not installed) and a trigger eval. `metadata.aliases` keeps the
  AiScientist name each one replaces.
  - `single-cell/annotate-clusters-by-markers` (was `annotate_clusters_by_markers_v2`, which
    superseded `annotate_clusters_by_markers`)
  - `single-cell/compare-conditions-by-celltype` (was `condition_by_celltype`)
  - `single-cell/compare-two-groups-with-scanpy` (was `pairwise_de`)
  - `single-cell/crossvalidate-scgpt-vs-leiden` (was `crossvalidate_scgpt_vs_leiden`)
  - `single-cell/prioritize-disease-genes-with-atlas` (was `atlas_disease_genes`)
  - `single-cell/score-gene-signatures-with-scanpy` (was `score_signature`)
  - `crispr-screens/compare-perturbations-to-control` (was `perturbation_de_vs_control`)
  - `crispr-screens/filter-escapers-with-mixscape` (was `mixscape_escape_filter`); the pertpy call
    now works on pertpy 1.4, where `labels` became `pert_key`
  - `crispr-screens/rank-perturbations-by-edistance` (was `perturbation_edistance`); the docs no
    longer say it equals pertpy's `edistance`, which uses plain Euclidean distances
  - `variants/build-variant-db-with-tiledbvcf` (was `build_variant_db_tiledbvcf`); a re-run no
    longer ingests every VCF again and doubles the records
  - `variants/normalize-vcf-with-bcftools` (was `normalize_vcf`); splits multiallelic records
    before atomizing, so a multiallelic SNP no longer turns into `*` records
  - `variants/prioritize-clinical-variants` (was `clinical_variant_prioritization`)
  - `variants/qc-vcf-callset` (was `vcf_qc_stats`); Het/Hom now reads het and hom-alt counts, and
    the call rate counts hom-ref calls
  - `variants/write-variant-tables` (was `variant_output_tables`)
  - `literature/recover-paper-pdfs` (was `literature-corpus-recovery`), instruction only: the ladder of
    legal sources, from open-access APIs to institutional access, and the eight checks of every PDF
- Categories `crispr-screens`, `variants` and `literature` (plugin entries and CODEOWNERS lines).
- `single-cell/qc-snrna-with-cellqc-standalone` 1.0.0 (core): CellQC cohort QC for 10x
  snRNA-seq with bash and conda only, tested with cellqc 0.3.6 (DoubletFinder 2.0.6,
  Snakemake 9.22.0, Python 3.12.14).
- `aiscientist-skill` CLI: `new`, `validate`, `sync`, `list`, `test`, `eval`, `review`,
  `package`, `site`.
- JSON Schema for skill frontmatter, with registry fields (status tier, version, compute,
  scheduler, network, secrets) in `metadata`.
- Content checks for personal paths, emails, real Slurm accounts and tokens.
- Generated `catalog.json`, README catalog and Claude Code plugin marketplace.
- CI (validate, lint, dependency audit, test matrix, permission review), on-demand trigger
  evals, tagged releases with reproducible zips and checksums, and a searchable catalog site.
- Governance (tiers, review, versioning, releases), security policy, code of conduct,
  citation metadata, CODEOWNERS, Dependabot.
- Catalog site with status pills, declared requirements, tag filtering and copyable install
  commands; CI build job that packages release assets on every change.
