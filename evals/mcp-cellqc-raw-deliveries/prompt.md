---
description: Selects the configured single-cell MCP workflow for a realistic service request.
tags: [trigger, single-cell, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

The cellqc MCP service is already registered and has access to our raw and filtered Cell Ranger deliveries. Please run ambient correction and doublet removal for these nuclei, inspect the retention ledger and hand the resulting checkpoints to downstream analysis. The BAM is absent.
