---
name: qc-cellranger-with-mcp
description: Run ambient correction, filtering and doublet removal through an already configured CellQC MCP service for raw and filtered Cell Ranger deliveries. Use when this service is present and QC checkpoints must feed another analysis service; keep the standalone CellQC method for deployments without the MCP service.
license: MIT
metadata:
  category: single-cell
  version: 0.1.2
  status: community
  tags: mcp, cellqc
  tested-with: aiscientist-mcp-cellqc 0.0.5, common 0.0.4; image and default Docker CLI smoke; frozen CellQC 0.3.6 environment; strict cohort parity and website acceptance pending
  compute: 'Service default: 16 CPUs, 80 GB, 8 hours; size the real cohort separately'
  requires-gpu: 'false'
  scheduler: optional
  requires-network: install
  requires-secrets: none
  mcp-server: cellqc
  mcp-package-version: 0.0.5
  image: "docker://ghcr.io/lijinbio/mcp-cellqc@sha256:d0f456eb4c76c848dc671dfc2e9bcae5221e5bfd5363b2acd8d3769749e3b500"
  cpus: "16"
  mem_gb: "80"
  time_limit: "02:00:00"
---

# QC Cell Ranger deliveries through MCP

Use the registered `cellqc` service for raw 10x deliveries, retaining the current
`qc-snrna-with-cellqc-standalone` workflow when that service is unavailable. Discover the real
client tool names and schemas; do not assume an unregistered `mcp_` alias exists. This new
community skill pins the upstream `cellqc-v0.0.5` release image; the released standalone skill keeps its own image.

The 0.0.3 validation image failed strict parity: its full three-sample run retained 34,274 cells
in total, but human barcode membership and doublet/ambient diagnostics differed from the
original environment. Version 0.0.4 restores all 508 original scientific package archives and
isolates the MCP interpreter. Version 0.0.5 preserves that environment and fixes activation
for the default Docker entry point. Its image/default-CLI smoke passed; the frozen-environment
full-cohort comparison and the 0.0.5 website acceptance are still pending. Require recorded
strict parity and website acceptance before cutover; successful task completion alone does
not establish interchangeable results.

## Admit the correct inputs

`run_cellqc` accepts `dataset`, additional `dataset_paths`, optional library `samples`,
`analysis_id`, and QC settings. The operator sets `CELLQC_DATASET` and `CELLQC_READ_ROOTS`.
Paths must exist on the service host. Use raw **and** filtered matrices for ambient correction;
an `.h5ad` alone calls for the scRNA service's `run_scanpy_qc`, not invented raw droplets.
Supported deliveries include H5 files, matrix folders, and the supported Cell Ranger archives.

Check species and chemistry inferred from Cell Ranger metadata. Confirm `nreaction` from
library preparation when it is not known; it is not inferred from gene expression.

## Submit meaningful settings

Choose `max_pct_mt`, `min_counts`, and `min_features` for cells versus nuclei and the tissue.
State which `ambient_method` is applied and which `ambient_compare` is only a diagnostic.
Keep `doublet_decider`, chemistry/reaction assumptions, and `seed` in provenance. Do not run
another doublet-removal tool after this pipeline merely because it is available.

Call `run_cellqc` once and retain `analysis_id`, `task_id`, and the real Slurm `job_id` if
returned. Poll `cellqc_job_status(analysis_id, task_id)` until `COMPLETED`. Inline calls wait
inside an existing allocation; local execution requires that process/container to stay alive.
Use a new attempt only after the active one finishes. Failure or missing dependencies are not QC.

## Validate the cohort and handoff

Check every library's raw, filtered, and retained counts, ambient estimates, applied correction,
mitochondrial genes, doublet calls, and removal ledger. BAM-dependent nuclear-fraction evidence
must be labeled unavailable when no BAM was supplied. Species remain separate; do not merge
incompatible gene spaces. A large removal fraction or ambient disagreement requires inspection,
not silent suppression of the warning.

For a multi-species result, iterate every entry in the `checkpoints` mapping and collect each
entry's `checkpoint`; the singular `checkpoint_path` and `adata_qc.h5ad` represent only the
first species. Never infer that collecting that one file transfers the complete cohort.

Collect only the advertised artifacts and checkpoint outputs from the service. Use the
application's explicit checkpoint collector or an operator-configured scRNA handoff; an absolute
server path alone does not transfer a file. When QC is rerun and upstream checkpoints change,
start a new downstream scRNA analysis instead of reusing old clustering.

Report parameters, applied-versus-compared methods, sample/species counts, versions, task IDs,
all missing evidence and delivered checkpoints. Source parity tests and a new MCP Docker image build exist;
the target site's full-cohort and website acceptance evidence determines cutover. This skill
alone does not assert that deployment acceptance has completed.
