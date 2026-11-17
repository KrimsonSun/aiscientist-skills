---
description: Selects the configured literature MCP workflow for a realistic service request.
tags: [trigger, literature, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

The literature MCP service is configured with our local paper corpus. Retrieve evidence about PRPF31 dosage sensitivity and help decide whether a few top search passages are enough or whether I need a complete corpus curation. Keep citations and coverage limits visible.
