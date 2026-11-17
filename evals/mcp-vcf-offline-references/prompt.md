---
description: Selects the configured variants MCP workflow for a realistic service request.
tags: [trigger, variants, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

I have a GRCh37 VCF and our variant-annotation MCP service has the matching offline VEP resources. Annotate it, keep rare relevant genes and deliver the full tables. If the cache fails, do not transmit the variants to an external service.
