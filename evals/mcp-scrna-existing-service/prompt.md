---
description: Selects the configured single-cell MCP workflow for a realistic service request.
tags: [trigger, single-cell, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Our MCP client is connected to the scrna-analysis service. I have an admitted retinal AnnData count matrix from six real samples and want QC, clustering, sample-aware differential expression and marker annotation. Please use the available service and carry its results correctly between steps.
