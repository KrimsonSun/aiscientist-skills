# Changelog

All notable changes to this repository are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the registry uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.9] - 2026-11-16

### Added

- `literature/query-retigene-papers-with-aiscientist-mcp` 0.0.1: answers a question about inherited
  retinal disease genes by calling the `retigene-rag` 0.0.1 MCP server of
  [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp), pinned by image digest. Gene table
  lookups (`get_gene`, `find_genes`) answer what RetiGene curates about a gene and which genes meet
  conditions, with exact lists and counts and no model call: with Claude Haiku, 27 questions asked
  twice scored 53 of 54, against 16 of 54 from searching the papers alone. For what the papers say:
  keyword search over every sentence, embedding search over passages, and a corpus-wide curation that
  grades each gene from its own sentences with verbatim quotes, PMIDs and pages (ten runs listed the
  curator's 15 A genes as A, at $0.31-0.39 and 2.5-3.5 min per question with Claude Haiku). It needs
  no secret of its own: the model comes from whoever runs the server. It comes with the trigger evals
  `list-haploinsufficient-genes-in-retigene` and `list-genes-by-retigene-table-conditions`.

## [0.2.8] - 2026-11-16

### Fixed

- `variants/annotate-vcf-with-mcp` 0.1.2 pins variant-annotation MCP 0.0.3
  (`ghcr.io/lijinbio/mcp-variant-annotation@sha256:b013f4fcd951…`): a VCF without `##contig` lines is
  normalized after taking the reference's contigs, and SpliceAI starts from an environment
  reached at another path (lijinbio/aiscientist-mcp#9). Recorded acceptance evidence refers to 0.0.2.

## [0.2.7] - 2026-11-15

### Fixed

- `single-cell/analyze-scrna-with-mcp` 0.1.4 pins scrna-analysis MCP 0.0.6
  (`ghcr.io/lijinbio/mcp-scrna-analysis@sha256:f979615ed1ed…`), in which a bare `input` name finds
  a checkpoint handed off by another analysis of the same run (lijinbio/aiscientist-mcp#7).
  The scientific stack is unchanged from 0.0.5; recorded acceptance evidence refers to 0.0.5.

## [0.2.6] - 2026-11-13

### Changed

- The seven native MCP skills pin the upstream `ghcr.io/lijinbio/mcp-*` release images
  instead of the contributor's fork validation images, each with a patch version bump:
  `literature/read-evidence-with-mcp` 0.1.2 (`mcp-literature@sha256:05ab531fb89a…`);
  `single-cell/analyze-scrna-with-mcp` 0.1.3 (`mcp-scrna-analysis@sha256:1c978c154071…`);
  `single-cell/annotate-cells-with-scgpt-mcp` 0.1.1 (`mcp-scgpt-annotation@sha256:7ee18dc0df9f…`);
  `single-cell/qc-cellranger-with-mcp` 0.1.2 (`mcp-cellqc@sha256:d0f456eb4c76…`);
  `utilities/inspect-data-and-draw-schematics-with-mcp` 0.1.1 (`mcp-data-utilities@sha256:e3afbd62473f…`);
  `variants/annotate-vcf-with-mcp` 0.1.1 (`mcp-variant-annotation@sha256:a1861a81a36d…`);
  `variants/rank-phenotype-differentials-with-mcp` 0.1.2 (`mcp-phenotype-diagnosis@sha256:d20ed2dc2e57…`).
  The upstream images are built by the release workflow from the same source tree as the
  validated fork builds (`5981cc7`); recorded acceptance evidence refers to the fork builds.
- First upstream release of the 0.2.2–0.2.5 changes, which were published only as fork
  validation prereleases.

## [0.2.5] - 2026-11-13

### Fixed

- Literature and phenotype MCP skills 0.1.1 pin the published 0.0.4 images.
  Complete literature evidence is transferred through bounded MCP resources with
  identity, size, offset and SHA-256 checks. Local real-protocol tests passed;
  released-image and selected-session website gates remain pending. The earlier
  website LIRICAL-only result is retained as failed literature-adjudication evidence.
- `single-cell/analyze-scrna-with-mcp` 0.1.2 records the now-passing final 0.0.5
  native HPC regression. Its image pin is unchanged; website acceptance remains
  separate. Historical 0.2.4 pending-test provenance is preserved.

## [0.2.4] - 2026-11-13

### Fixed

- `single-cell/analyze-scrna-with-mcp` 0.1.1 pins the published scRNA MCP 0.0.5 image.
  Its provenance records the frozen Scanpy 1.11.5 scientific stack, explicit
  `deployed-auto-combat-v1` default policy, optional explicit Harmony, and private
  nullable-metadata normalization. Released SIF CLI/schema/file verification passed;
  full native and website acceptance remain separate pending gates. Earlier
  same-environment algorithm parity is not presented as old-environment equivalence.
  No other skill image changes in this registry release.

## [0.2.3] - 2026-11-13

### Fixed

- `single-cell/qc-cellranger-with-mcp` 0.1.1 pins the published CellQC MCP 0.0.5 image
  by its release digest. It retains the frozen scientific environment from 0.0.4 and
  fixes default Docker entry-point activation. The skill distinguishes the passing
  image/CLI smoke from still-pending strict full-cohort parity and website acceptance.
  No other skill image changes in this registry release.

## [0.2.2] - 2026-11-12

### Added

- Seven community, instruction-only MCP migration skills for scRNA analysis, CellQC, scGPT,
  literature, variant annotation, phenotype ranking and data utilities, with trigger evals.
  They require an actually registered service, preserve existing standalone/legacy workflows,
  distinguish real and synthetic acceptance evidence, and pin published fork validation images
  with explicit CPU, memory and time requests. Registration and trusted reference/model settings
  remain deployment configuration; these preview pins do not change existing production tools.
- The `utilities` category for bounded dataset inspection and deterministic schematic rendering.

### Fixed

- `single-cell/explore-atlas-expression-with-aiscientist-mcp`: use AiScientist's typed MCP
  tools and `atlas_write_report` for the query report. Standalone MCP and CLI clients retain
  the server's `write_report` name; dataset binding, execution settings and artifact collection
  are supplied by the AiScientist bridge.

## [0.2.1] - 2026-11-10

### Added

- `knowledge-graph/answer-eye-questions-with-visionkb-kg` 0.0.1, instruction only, and the
  `knowledge-graph` category (plugin entry and CODEOWNERS line): answers knowledge questions about
  eye genes, cell types, diseases and datasets with the read-only VisionKB API (entities, atlas
  summaries, typed Biolink relationships with `knowledge_level`, evidence, datasets with bind
  records), and names the equivalent `visionkb-kg` MCP tools. It states the expression-edge rule,
  the ambient-RNA and doublet caveats (known issue KI-1) and that a missing edge is not evidence of
  non-expression. `scripts/vkb_client.py` pages by rows received (the API trims pages to its
  character cap) and labels single pages `complete`, `partial` or `trimmed: n of total`, with tests
  against a fake trimming API. Tested on the KG release `visionkb-2026.11.0` served by
  visionkb-api 0.1.1. It comes with the trigger eval `ask-eye-knowledge-graph-expression-and-disease`.
- `literature/read-whole-corpus-with-claude` 0.0.1: answers a question from a chunked full-text
  corpus by having Claude Haiku read every passage, ten per call, as numbered sentences, and keep
  the sentences that bear on it (verbatim, with PMID and page). `scripts/read_corpus.py` estimates
  the cost before a read, resumes a read that stopped, and builds a table of every HGNC gene the
  evidence names for a gene-list question. Tested on the RetiGene corpus (39,563 passages). It
  comes with the trigger eval `list-every-gene-from-paper-corpus`.

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
