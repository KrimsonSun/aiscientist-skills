---
description: Selects explore-atlas-expression-with-aiscientist-mcp for a request it should handle.
tags: [trigger, gene-expression]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

We have the human retina snRNA-seq atlas as one big h5ad (about 3 million nuclei, raw counts, with majorclass, celltype, region and donor in obs and a UMAP). Show me LRAT across the retinal cell types: a dot plot, a violin plot and a UMAP feature plot, plus a table I can cite and a short write-up. Someone also asked about CRALBP, so include that if the name works.
