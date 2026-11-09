<div align="center">

# AiScientist Skills

**Tested, reproducible agent skills for scientific data analysis.**

[![CI](https://github.com/lijinbio/aiscientist-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/lijinbio/aiscientist-skills/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/lijinbio/aiscientist-skills?sort=semver)](https://github.com/lijinbio/aiscientist-skills/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-8A2BE2)](https://agentskills.io/specification)

[Catalog](#catalog) · [Install](#install) · [Contribute](CONTRIBUTING.md) · [Governance](docs/governance.md) · [Security](SECURITY.md) · [Browse online](https://lijinbio.github.io/aiscientist-skills/)

</div>

---

This is the skill registry for **AiScientist**, an agent that plans and runs data analyses for
scientists. Each skill packages one analysis method: the environment setup, the commands, how
to choose parameters, and the checks that show whether the result can be trusted. Commands come
from runs that completed end to end, not from documentation. The catalog starts with
computational biology (single-cell genomics) and is organised by category so other domains can
be added alongside it.

Skills use the open [Agent Skills](https://agentskills.io/specification) format, so they also
work in Claude Code, the Claude apps and API, and any other agent that reads `SKILL.md`.

## Catalog

Status: 🟢 **core** maintained by the registry owners · 🔵 **verified** reviewed by a domain
expert · ⚪ **community** passed automated checks, not yet reviewed. See
[governance](docs/governance.md#tiers).

<!-- BEGIN SKILLS -->

### crispr-screens

Pooled CRISPR screens with a single-cell readout (Perturb-seq): escaping cells, per-perturbation differential expression and effect sizes.

| Skill | Status | Version | What it does |
| --- | --- | --- | --- |
| [`compare-perturbations-to-control`](skills/crispr-screens/compare-perturbations-to-control/) | ⚪ community | 1.0.0 | Per-perturbation differential expression against one shared non-targeting control in a pooled CRISPR screen with single-cell readout (Perturb-seq, CROP-seq, CRISPRi or CRISPRa) with scanpy rank_genes_groups (Wilcoxon, explicit reference), from an AnnData with a guide or perturbation column to one DE table per perturbation, a summary table with a target self-knockdown positive control, and the genes shared across perturbations. |
| [`filter-escapers-with-mixscape`](skills/crispr-screens/filter-escapers-with-mixscape/) | ⚪ community | 1.0.0 | Label and remove escaping cells in a pooled CRISPR screen with single-cell readout (Perturb-seq, CROP-seq) with Mixscape from pertpy, from a log-normalized AnnData with a guide or perturbation column and a non-targeting control to adata_mixscape.h5ad without the non-perturbed (NP) cells, plus the NP fraction of every perturbation. |
| [`rank-perturbations-by-edistance`](skills/crispr-screens/rank-perturbations-by-edistance/) | ⚪ community | 1.0.0 | Rank the perturbations of a pooled CRISPR screen with single-cell readout (Perturb-seq, CROP-seq, CRISPRi or CRISPRa) by E-distance (energy distance) to the non-targeting control in PCA space, with a label-permutation test and Benjamini-Hochberg correction, from an AnnData with a guide or perturbation column to a ranked CSV, the list of hits to carry into differential expression, and an optional perturbation-by-perturbation distance matrix. |

### literature

Scientific literature: recovering, verifying and assembling full-text paper corpora for review and retrieval.

| Skill | Status | Version | What it does |
| --- | --- | --- | --- |
| [`query-retigene-papers-with-aiscientist-mcp`](skills/literature/query-retigene-papers-with-aiscientist-mcp/) | ⚪ community | 0.0.1 | Answer a question about the RetiGene papers (about 1,700 full-text papers on inherited retinal disease), such as "What are haploinsufficient genes in RetiGene papers?", by calling the retigene-rag MCP server from the aiscientist-mcp repository. |
| [`read-whole-corpus-with-claude`](skills/literature/read-whole-corpus-with-claude/) | ⚪ community | 0.0.1 | Answer a question from a chunked full-text literature corpus completely, by having Claude Haiku read every passage (not the top-k of a search) and return the numbers of the sentences that bear on it, so every quote is verbatim. |
| [`recover-paper-pdfs`](skills/literature/recover-paper-pdfs/) | ⚪ community | 1.0.0 | Recover and assemble a corpus of scientific paper PDFs from a list of PMIDs or DOIs through a ladder of legal sources (open-access APIs, PMC and Europe PMC, publisher open access, then the user's institutional access through the campus network, VPN or library discovery search), verifying every PDF and tracking each paper in a manifest. |

### single-cell

Single-cell and single-nucleus RNA-seq: QC, integration, annotation and downstream analysis.

| Skill | Status | Version | What it does |
| --- | --- | --- | --- |
| [`annotate-clusters-by-markers`](skills/single-cell/annotate-clusters-by-markers/) | ⚪ community | 1.0.0 | Reference-free cell-type annotation of clusters from a curated marker panel with scanpy. |
| [`compare-conditions-by-celltype`](skills/single-cell/compare-conditions-by-celltype/) | ⚪ community | 1.0.0 | Condition-vs-control differential expression within each cell type (for example KO vs WT, or disease vs control, per cell type) with scanpy rank_genes_groups (Wilcoxon, explicit reference group). |
| [`compare-two-groups-with-scanpy`](skills/single-cell/compare-two-groups-with-scanpy/) | ⚪ community | 1.0.0 | Differential expression between two named groups of cells (for example disease vs control, or cluster 3 vs cluster 5) with scanpy rank_genes_groups (Wilcoxon) and an explicit reference group, from an AnnData file to a ranked CSV table and a JSON summary. |
| [`crossvalidate-scgpt-vs-leiden`](skills/single-cell/crossvalidate-scgpt-vs-leiden/) | ⚪ community | 1.0.0 | Cross-validate scGPT per-cell cell-type predictions against the data's own structure. |
| [`explore-atlas-expression-with-aiscientist-mcp`](skills/single-cell/explore-atlas-expression-with-aiscientist-mcp/) | ⚪ community | 0.0.1 | Answer a gene expression query such as "show LRAT across retinal cell types" on a large single-cell or single-nucleus atlas .h5ad with raw counts, by calling the atlas-expression-exploration MCP server from the aiscientist-mcp repository. |
| [`prioritize-disease-genes-with-atlas`](skills/single-cell/prioritize-disease-genes-with-atlas/) | ⚪ community | 1.0.0 | Prioritize disease-associated genes by combining an existing condition-vs-control differential expression result (per cell type) with a precalculated cell-type atlas, offline. |
| [`qc-snrna-with-cellqc-standalone`](skills/single-cell/qc-snrna-with-cellqc-standalone/) | 🟢 core | 1.2.0 | Run the CellQC pipeline (ambient correction, count/feature/mitochondrial filtering, doublet calling, nuclear fraction) over a cohort of 10x Cell Ranger libraries by hand, with bash plus conda or a container, from installing cellqc to validating result/metrics.csv. |
| [`score-gene-signatures-with-scanpy`](skills/single-cell/score-gene-signatures-with-scanpy/) | ⚪ community | 1.0.0 | Score every cell for one or more gene signatures with scanpy score_genes (the signature's mean expression minus that of a matched random control gene set) and summarise each score per group, for example cell type by condition, as n, mean, median and IQR, with per-cell scores, box plots and a JSON coverage report. |

### variants

DNA variant analysis from VCF files: normalization, callset QC, result tables, research triage and variant databases.

| Skill | Status | Version | What it does |
| --- | --- | --- | --- |
| [`build-variant-db-with-tiledbvcf`](skills/variants/build-variant-db-with-tiledbvcf/) | ⚪ community | 1.0.0 | Build and query a TileDB-VCF variant database for a cohort with tiledbvcf-py - ingest many indexed single-sample VCFs into one compressed sparse-array dataset (a re-run adds only new samples, with no re-merging), query genomic regions across all or selected samples, and export the matching records (sample, contig, position, alleles, genotype) to a TSV with per-sample counts. |
| [`normalize-vcf-with-bcftools`](skills/variants/normalize-vcf-with-bcftools/) | ⚪ community | 1.0.0 | Normalize a VCF with bcftools norm before annotation or ClinVar/gnomAD matching - split multiallelic sites into biallelic records, atomize MNPs into SNPs, then left-align and trim indels against the reference FASTA of the same build - writing an indexed normalized.vcf.gz and a JSON of record counts before and after. |
| [`prioritize-clinical-variants`](skills/variants/prioritize-clinical-variants/) | ⚪ community | 1.0.0 | Rank annotated variants into research-triage tiers (ClinVar pathogenic, likely pathogenic, VUS favouring pathogenic, VUS, likely benign, benign) from ClinVar significance used verbatim, gnomAD allele frequency against a dominant or recessive disease-model cutoff and the ACMG BA1 5 percent rule, and in-silico predictors (SIFT, PolyPhen, REVEL, CADD, AlphaMissense) as supporting evidence only. |
| [`qc-vcf-callset`](skills/variants/qc-vcf-callset/) | ⚪ community | 1.0.0 | Judge whether a germline VCF callset is trustworthy before interpreting any variant - Ti/Tv, Het/Hom, SNP, indel and multiallelic counts, sample count and genotype call rate from bcftools stats (falling back to cyvcf2, then to a plain-Python Ti/Tv scan) - and flag values outside the expected human WGS or WES ranges. |
| [`write-variant-tables`](skills/variants/write-variant-tables/) | ⚪ community | 1.0.0 | Write the five standard variant-annotation result tables - consequence, impact and ClinVar-significance distributions, a ClinVar pathogenic and likely-pathogenic list, and a shortlist of rare, damaging variants not in ClinVar - plus a JSON summary, from an annotated per-variant TSV (VEP consequence and impact, SIFT, PolyPhen, max population AF, rsID, ClinVar significance), in pure Python without re-parsing the VCF or re-running VEP. |

<!-- END SKILLS -->

## Install

### Claude Code

```bash
/plugin marketplace add lijinbio/aiscientist-skills
/plugin install single-cell@aiscientist-skills
```

Each category is a plugin, so you install only the domains you need.

### Claude apps

Build a skill's `.zip` and upload it under **Settings → Capabilities → Skills**:

```bash
git clone --depth 1 https://github.com/lijinbio/aiscientist-skills.git && cd aiscientist-skills
aiscientist-skill package --per-skill --out dist   # dist/<skill>-<version>.zip, one per skill
```

### Any agent, or by hand

A skill is a folder. Copy it into the agent's skills directory:

```bash
git clone --depth 1 https://github.com/lijinbio/aiscientist-skills.git
cp -R aiscientist-skills/skills/single-cell/qc-snrna-with-cellqc-standalone ~/.claude/skills/
```

### From an application (AiScientist)

Pin a release tag, never `main`. Every release ships:

| Asset | Use |
| --- | --- |
| `catalog.json` | machine-readable index: name, version, status, tags, description, and declared requirements (compute, GPU, scheduler, network, secrets) for every skill |
| `aiscientist-skills-<version>.zip` | every skill folder at its catalog `path` (`skills/<category>/<name>/`), reproducibly zipped |
| `SHA256SUMS` | checksums for the bundle and `catalog.json` |

`catalog.json` is also committed at the repository root and is regenerated by CI on every
change, so a given commit always has a matching index.

## The skill contract

```
skills/<category>/<skill-name>/
├── SKILL.md        # required: frontmatter + instructions
├── scripts/        # optional: code the skill runs (linted, reviewed and tested)
├── tests/          # optional: pytest tests for scripts/, run in CI
├── references/     # optional: long reference material, loaded on demand
└── assets/         # optional: templates and small example files
```

The frontmatter follows the Agent Skills specification. Registry fields live in `metadata`,
whose values must be strings:

```yaml
---
name: qc-snrna-with-cellqc-standalone
description: What it does and when to use it (this is what the agent matches requests against).
license: MIT
compatibility: Requires bash, coreutils, tar, awk and conda or mamba; Slurm optional.
metadata:
  category: single-cell
  version: "1.0.0"              # semver of the skill itself
  status: core                  # core | verified | community
  author: "Jin Li"
  tags: "snrna-seq, qc, 10x-genomics"
  tested-with: "cellqc 0.3.6, Python 3.12"
  compute: "16 CPUs, 80 GB requested (25.6 GB peak), 20 min for 4 libraries"
  requires-gpu: "false"
  scheduler: "optional"         # none | optional | required
  requires-network: "install"   # none | install | runtime
  requires-secrets: "none"      # or comma-separated env var names
---
```

The full JSON Schema is in
[`src/aiscientist_skills/schemas/skill.schema.json`](src/aiscientist_skills/schemas/skill.schema.json).

## Tooling

`aiscientist-skill` is a small Python CLI (`src/aiscientist_skills/`) that runs the same checks
locally that CI runs. It is a normal Python package, so install it with whatever you already
use; the commands below are the same afterwards.

```bash
# without a clone, straight from GitHub (pin a tag for reproducibility)
pip install git+https://github.com/lijinbio/aiscientist-skills.git
pipx install git+https://github.com/lijinbio/aiscientist-skills.git@v0.2.0
uvx --from git+https://github.com/lijinbio/aiscientist-skills.git aiscientist-skill --help

# from a clone, for contributing (pick one)
pip install -e '.[dev]'                        # into the environment you have active
pipx install -e '.[dev]'                       # isolated, on your PATH
uv sync                                        # .venv from uv.lock; prefix commands with `uv run`
conda create -n aiscientist-skills python=3.12 pip && conda activate aiscientist-skills && pip install -e '.[dev]'
```

The CLI always operates on a checkout of this repository (it locates the root by
`.claude-plugin/marketplace.json`), so the GitHub install is for using the tool against a clone
or a fork without installing into it.

```bash
aiscientist-skill new single-cell/my-skill --author "Your Name"
aiscientist-skill sync                  # regenerate README catalog, marketplace.json, catalog.json
aiscientist-skill validate              # schema, structure, links, leaked paths/accounts/secrets
aiscientist-skill test                  # each skill's tests/
aiscientist-skill eval                  # trigger evals via `claude plugin eval` (uses model credits)
aiscientist-skill review --base main    # what a branch asks for beyond the permission baseline
aiscientist-skill list --status core
```

CI pins the tooling's dependencies with `uv.lock` so every run resolves the same versions;
nothing else depends on uv.

### What runs on every pull request

| Gate | Checks |
| --- | --- |
| **Validate** | frontmatter against the JSON Schema; name matches its folder; category has a plugin; relative links resolve; no personal paths, emails, real Slurm accounts or tokens; files under 1 MB; generated files up to date |
| **Lint** | Ruff lint and format; `pip-audit` of the tooling's locked dependencies |
| **Test** | the tooling's test suite and every skill's `tests/`, on Python 3.11 and 3.14 |
| **Install** | `pip install '.[dev]'` from a clean interpreter, then `validate`; the tooling must work without uv |
| **Permission review** | any new runtime network access, secret, `allowed-tools` grant, GPU requirement, change to `scripts/` or tier change gets the `needs-security-review` label |
| **Evals** (on demand) | each skill gets selected for realistic requests ([evals/](evals/)) |

Reviewers are assigned by category through [CODEOWNERS](.github/CODEOWNERS).

## Principles

- **Has been run.** Code is copied from scripts that completed. Each skill says what it was
  tested on: data, versions, resources and runtime.
- **Self-contained.** Environment setup is included, versions are pinned, and the skill doesn't
  depend on anything outside its own folder.
- **Declares what it needs.** Compute, scheduler, network and secrets are in the frontmatter, so
  a runtime can enforce them and a reviewer can see them.
- **Validates its output.** A pipeline finishing doesn't make its result trustworthy, so each
  skill says which outputs to check and what a bad result looks like.
- **Reports honestly.** Failures, fallbacks and skipped steps are reported, not hidden.

## Citing

If skills from this registry contribute to a publication, cite the registry using the metadata in
[`CITATION.cff`](CITATION.cff) (GitHub shows a **Cite this repository** button), along with the
tools each skill runs.

## License

[MIT](LICENSE) © 2026 Rui Chen Lab, University of California, Irvine. Tools that skills call (CellQC, Snakemake, R packages and others) keep their own
licenses.
