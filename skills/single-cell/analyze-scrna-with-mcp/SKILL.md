---
name: analyze-scrna-with-mcp
description: Run QC, clustering, differential expression, enrichment and marker annotation through an already configured scrna-analysis MCP service. Use for an AnnData workflow when this service is available and its checkpoints and asynchronous task results must be carried between steps; retain the existing standalone workflow when it is not registered.
license: MIT
metadata:
  category: single-cell
  version: 0.1.4
  status: community
  tags: mcp, scrna-analysis
  tested-with: aiscientist-mcp-scrna-analysis 0.0.5 (0.0.6 changes only bare-name checkpoint lookup, unit-tested), common 0.0.4; frozen scientific Python 3.11.15 and Scanpy 1.11.5; released SIF CLI/schema/file verification and full native HPC regression passed; website acceptance is separate
  compute: 4 CPUs, 48 GB requested; 480 real cells x 1550 genes, 6 samples, 2 tissue regions; this is a regression subset, not full-atlas sizing
  requires-gpu: 'false'
  scheduler: optional
  requires-network: install
  requires-secrets: none
  mcp-server: scrna-analysis
  mcp-package-version: 0.0.6
  image: "docker://ghcr.io/lijinbio/mcp-scrna-analysis@sha256:f979615ed1ed98c61cf7a6cb1bba26fcd4076b119b17ff7d4f873647d7f43d18"
  cpus: "4"
  mem_gb: "48"
  time_limit: "01:00:00"
---

# Analyze single-cell data with the scRNA MCP service

Use the registered `scrna-analysis` service to execute analysis, preserving one `analysis_id`
through a dependent chain. This skill contains no replacement scientific implementation.

## Select an available execution path

Read the client's actual tool inventory and advertised schemas. Tool names below are the
server's native names; a host may qualify them. Do not invent a `mcp_` prefix or call an
unregistered name. If this service is absent, keep the currently available AiScientist tools
or the installed standalone analysis skill. This migration skill does not change their image,
install an unpublished release, or retire the legacy path. Its image pin names the upstream `scrna-analysis-v0.0.6` release.

The service operator binds `SCRNA_DATASET`, `SCRNA_READ_ROOTS`, and writable `AISCI_DATA_DIR`.
An explicit `dataset` must be admitted on the server host. Tool `input` selects a checkpoint
inside this analysis's `work/` or `artifacts/`; it is not a general filesystem reader.
A bare file name means `work/<name>`; from 0.0.6 it also finds a checkpoint that another
analysis of the same run handed off through `SCRNA_CHECKPOINT_ROOT`.

## Choose the calculation

| Tool | Use and important parameters |
| --- | --- |
| `run_scanpy_qc` | An AnnData input: inspect mitochondrial gene matching and set `min_genes`, `min_cells`, `max_pct_mt`, `n_top_genes` for the assay. |
| `run_doublet_detection` | An explicit additional doublet step only when upstream QC has not already removed doublets. |
| `run_integration` | Specify a real `batch_key`; omitted/`auto` selects ComBat under `deployed-auto-combat-v1`. Request `method="harmony"` explicitly for Harmony. Do not use biological condition as a technical batch without justification. |
| `run_clustering` | Set `n_pcs`, `n_neighbors`, `resolution`; inspect actual cluster sizes and embedding. |
| `run_de` | Inspect `groupby` and the advertised contrast parameters; retain tested group/reference and cell-count provenance. |
| `run_depth_matched_de` | A depth-matched sensitivity analysis with explicit `groupby`, `reference`, and optional `stratify_by`; not a substitute for independent replicates. |
| `run_enrichment` | Enrich DE tables against operator-staged GMT `gene_sets`; preserve the background and tested gene counts. |
| `run_gsea_prerank` | Analyze ranked gene lists; report ties, set coverage, permutations, and configured gene-set sources. |
| `run_pseudobulk_de` | Replicate-aware counts using `sample_key`, `condition_key`, and optional `group_key`; never treat individual cells as biological replicates. |
| `run_composition` | Compare group proportions by real sample and condition; retain low-count and replication caveats. |
| `run_marker_annotation` | Apply curated `reference` or explicit `panel`, `discriminators`, and `cluster_key`. The reference infers species from genes; there is no `species` argument. |

Follow the checkpoint dependencies exposed by the tools. QC normally precedes clustering,
then DE and marker annotation. Enrichment consumes prior DE/rank tables. Do not interpret a
QC result with zero mitochondrial matches as evidence that high-mitochondrial cells were removed.

## Complete each task and carry outputs

Save the returned `analysis_id` and `task_id`. With Slurm/local execution, poll
`scrna_job_status(analysis_id, task_id)` until `COMPLETED`; retain a returned Slurm `job_id`.
A failure is a failed analysis, even if partial files exist. Inline calls already wait inside
the caller's allocation. Do not submit two writers to one analysis concurrently.

Use `artifact_root` for downloadable artifacts and `checkpoint_path` for the actual AnnData.
These are server-side paths: the application must explicitly collect them. An operator can
bind `SCRNA_CHECKPOINT_ROOT` for a CellQC handoff. Imported upstream checkpoints are tracked;
if CellQC later changes one, use a new `analysis_id` when the server refuses the old chain.
Never combine old clustering with replacement QC. `rerun=true` forces another attempt with
unchanged inputs; it is not permission to bypass the upstream-change check.

## Validate and report

Check cell/gene retention, counts-layer provenance, batch and sample identities, group sizes,
full DE tables, multiple-testing columns, and marker concordance. Preserve warnings and
non-estimable groups. Report thresholds, seeds, references, versions, task IDs and collected
artifacts. A table preview is not the complete result.

The 0.0.3 native image matched the original algorithms on a public HECA subset in the
same newer dependency environment: 480 observed cells, 6 samples, fovea/periphery, Rod/BC,
1,550 selected genes. That did not establish parity with the old production environment;
a subsequent comparison found marker-score and label differences.

The 0.0.5 image, whose scientific stack the pinned 0.0.6 image keeps, instead freezes the deployed scientific Python 3.11.15 / Scanpy 1.11.5
stack. The original 63 scientific packages retain their archive and installed-file provenance;
12 additional packages are declared separately. The released SIF passed default CLI, complete
schema and 75-package / 13,117-file verification. Local image comparisons restored marker
parity (0.0.4) and default-auto ComBat parity (0.0.5) at the original tolerances. Final released
0.0.5 native HPC acceptance also passed on this regression subset. Website acceptance remains
a separate cutover gate; the earlier 0.2.4 registry recorded the then-pending native test.

For integration, retain the unchanged requested arguments and the returned `integration_policy`
record. Its `deployed-auto-combat-v1` policy makes omitted/`auto` select ComBat independently of
optional installed packages; `method_used` is the algorithm that actually ran. Harmony is
available only when requested explicitly. ComBat changes expression values; Harmony changes
an embedding, so preserve this distinction when comparing results. The obsolete missing-Harmony
fallback note is not reproduced as if a dependency were missing.

Modern AnnData nullable-string metadata is normalized only in a private input copy or imported
checkpoint. Labels, missing positions and expression datasets are preserved; retain
`input_compatibility_path` as provenance. The caller's file and global AnnData settings remain
unchanged. Subset regressions do not establish validity for every biological contrast or size
a full-atlas job.
