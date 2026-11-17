---
name: annotate-cells-with-scgpt-mcp
description: Transfer cell labels from an approved reference model through an already configured scgpt-annotation MCP service. Use for GPU inference on an AnnData query when the validated harness and model are staged, then check predictions against independent structure and markers; do not substitute it for a marker-only annotation or assume the service is installed.
license: MIT
metadata:
  category: single-cell
  version: 0.1.1
  status: community
  tags: mcp, scgpt-annotation
  tested-with: aiscientist-mcp-scgpt-annotation 0.0.3, common 0.0.4, torch 2.3.0, scGPT 0.2.4, scanpy 1.11.5, anndata 0.11.4; real GPU old/new parity on 480 HECA cells
  compute: NVIDIA V100 or A30, 4 CPUs, 48 GB requested; 480 cells x 36601 genes; final-image V100 inference 42.5 seconds; earlier A30 validation 40.8 seconds
  requires-gpu: 'true'
  scheduler: optional
  requires-network: install
  requires-secrets: none
  mcp-server: scgpt-annotation
  mcp-package-version: 0.0.3
  image: "docker://ghcr.io/lijinbio/mcp-scgpt-annotation@sha256:7ee18dc0df9f11ebc4cb9cc9ec417d99c2a94b1f664fe3561f78e88b0a954df9"
  cpus: "4"
  mem_gb: "48"
  time_limit: "01:00:00"
---

# Annotate cells with the scGPT MCP service

This is reference-model inference with the validated scGPT harness. It does not ask a language
model to name cells. Use the client's registered `scgpt-annotation` tools and advertised names;
if unavailable, retain the existing approved scGPT deployment. Do not invent an MCP prefix,
download unapproved weights, or change the released standalone workflow's environment. The pinned image is the upstream `scgpt-annotation-v0.0.3` release; external assets remain operator supplied.

## Verify external assets and GPU

The operator stages the validated `step1_preprocess.py`, `step2_inference.py` and helpers,
sets `SCGPT_REFACTOR`, and provides the trained reference through `SCGPT_MODEL_DIR`.
The reference requires `best_model.pt`, `vocab.json`, `id2type.json`, and `dev_train_args.yml`.
Harness and model are external, read-only assets; they are not bundled with this skill.
The MCP Python runtime is separate from the validated torch/CUDA scientific interpreter.

Use an authorized `.h5ad` query from `SCGPT_DATASET` or `SCGPT_READ_ROOTS`. An explicit
`model_dir` must be admitted by `SCGPT_MODEL_ROOTS`. GPU availability is checked by default;
`SCGPT_REQUIRE_CUDA=0` is an operator diagnostic setting, not evidence of GPU inference.

## Run and retrieve the result

Call `scgpt_annotate` with a stable `analysis_id` and optional admitted `dataset`/`model_dir`.
Poll `scgpt_job_status(analysis_id, task_id)` to `COMPLETED` for Slurm/local execution. Save the
Slurm job ID when present. Inline execution waits inside the caller's GPU allocation. A failed
call provides a task ID for inspecting its failure evidence; do not use stale predictions.

Collect `predictions_csv` under `artifact_root`, and verify one prediction per expected barcode.
The response contains `n_cells`, `n_cell_types`, `label_counts`, `species_harmonization`, and
`input_compatibility`. Read the per-cell confidence values from the CSV rather than assuming
that a high aggregate label count establishes accuracy.

The original case-folding rule is retained: uppercase names are used only when their vocabulary
overlap is at least five times the exact match count and at least 1,000 genes greater. A changed
rule explicitly reports the cross-species name-based orthology assumption. New AnnData nullable
string indices/metadata are converted only in a private working copy when needed by the old
scientific environment; `input_compatibility` records those fields. Expression values and the
original query are not rewritten by that storage conversion.

## Validate labels independently

Compare barcode-aligned predictions with clustering, canonical positive/discriminating markers,
and the expected tissue classes. Inspect low-confidence calls and discordant groups. The known
mouse-to-human retinal transfer needs particular care for glial and vascular labels. Retain
unassigned or uncertain results rather than forcing agreement. The existing
`crossvalidate-scgpt-vs-leiden` skill remains useful for that separate analysis.

A real V100 run on 480 public human-retina cells matched the original deployed harness's
barcode-aligned predictions and confidence values with zero differences at tolerance 1e-6,
using identical weights, scientific image and prepared query. Matched A30 runs also agreed
exactly between old and new workflows. Comparing A30 with V100 preserved all 480 labels but
changed 35 confidence values by at most 0.0026; record the GPU when comparing confidence.
Nullable-string compatibility
was exercised on a new AnnData checkpoint. This is migration parity, not an accuracy benchmark
or proof that a different model/species transfer is valid. Record the actual model/harness/image
identities, GPU, task IDs, cell counts, compatibility changes and collected outputs.
