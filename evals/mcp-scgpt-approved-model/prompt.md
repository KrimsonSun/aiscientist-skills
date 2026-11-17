---
description: Selects the configured single-cell MCP workflow for a realistic service request.
tags: [trigger, single-cell, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Our scgpt-annotation MCP service has a GPU and the approved retinal model and harness. Annotate this admitted human AnnData query, retrieve per-cell confidence, then explain how to check whether the labels agree with independent markers and clustering.
