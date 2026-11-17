---
name: inspect-data-and-draw-schematics-with-mcp
description: Inspect an admitted data file and render a conceptual Graphviz schematic through an already configured data-utilities MCP service. Use for bounded format/metadata triage or a reproducible workflow figure with that service; do not use schematics as data plots or assume an unregistered MCP tool exists.
license: MIT
metadata:
  category: utilities
  version: 0.1.1
  status: community
  tags: mcp, data-utilities
  tested-with: aiscientist-mcp-data-utilities 0.0.2, common 0.0.4, MCP 2.3.0, Python 3.14.3, Graphviz 2.44.0; real 1.35 GB HECA file and original PNG parity
  compute: 1 CPU, 4 GB requested; bounded inspection 12.9 seconds, schematic 0.5 seconds in the tested allocation
  requires-gpu: 'false'
  scheduler: optional
  requires-network: runtime
  requires-secrets: none
  mcp-server: data-utilities
  mcp-package-version: 0.0.2
  image: "docker://ghcr.io/lijinbio/mcp-data-utilities@sha256:e3afbd62473f9eba7ac4665964c4312a1272f684b1cd8b17a0a0d5a63add0396"
  cpus: "2"
  mem_gb: "8"
  time_limit: "00:30:00"
---

# Inspect files and draw schematics through MCP

Use the client's registered `data-utilities` service and actual advertised tool names. If it
is absent, keep existing `inspect_dataset`/`make_schematic` or the established standalone
workflow. Do not invent an MCP prefix or substitute an unpublished image. The pinned image is the upstream `data-utilities-v0.0.2` release. The operator must register its matching
service and tool catalog before use.

## Inspect before assuming the format

`inspect_dataset(path, analysis_id, rerun)` uses the bound `DATA_UTILITIES_DATASET` when `path`
is omitted. An explicit path must be within operator-approved `DATA_UTILITIES_READ_ROOTS` on
the service host. A remote-host path must be mapped by the client adapter; do not silently
read an unrelated local file when admission fails.

The tool returns `peek`, `description`, and `raw_data_to_llm`. The deterministic evidence includes
magic bytes, size, VCF assembly/sample facts, HDF5 shape/tree metadata, table columns, or an
unknown/binary descriptor. Only the bounded file head and metadata are read; matrix values are
not loaded for this inspection. A malformed or unknown format remains best-effort evidence,
while missing/disallowed files and external HDF5 file links are errors.

An optional explicitly configured model may summarize the bounded evidence. Inspect the
reported source: without a model the original deterministic fallback is expected. Raw file
samples can reach that configured endpoint when `raw_data_to_llm=true`. Large inspections return a marked `response_omitted` preview and `full_result` points to a
complete per-attempt JSON under `artifact_root`; polling uses the same bounded preview.
A description is not new evidence for an assembly, sample, gene or row count absent from `peek`.

## Render a conceptual figure

`make_schematic(source, basename, analysis_id, rerun)` takes Graphviz DOT text and creates a
PNG plus its auditable DOT source. It is deterministic rendering; it does not call a model to
draw pixels. Use the analysis tools for figures computed from data. The server sanitizes the
basename and confines outputs to `artifacts/figures/`; external image/file references are refused.

Check returned `width`, `height`, aspect warnings and the actual image before embedding it.
A missing Graphviz dependency is a failed figure, even if its DOT source was saved. The result's
`figure` is relative to `artifact_root`; absolute paths refer to the server and require explicit
artifact collection by the client.

These short tools default to inline execution. If configured for Slurm/local, poll
`data_utilities_job_status(analysis_id, task_id)` until `COMPLETED`. Retain task IDs and any
Slurm job ID; do not interpret a pending or failed call as a generated output.

## Evidence for this migration

The service inspected the real public HECA object (265,767 cells x 36,601 genes, 1.35 GB), reading
262,144 head bytes plus HDF5 metadata. Its structured inspection matched the original code.
A real Graphviz 2.44.0 workflow figure matched the old renderer's PNG bytes. These checks cover
format triage and rendering, not biological validity or the optional model-description path.
Report the actual observed format, boundedness, model use, dimensions, warnings and artifact paths.
