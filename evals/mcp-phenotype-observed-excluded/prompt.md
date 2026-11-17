---
description: Selects the configured variants MCP workflow for a realistic service request.
tags: [trigger, variants, mcp]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Use our already connected phenotype-diagnosis MCP service for a synthetic case: the person has night blindness but no hearing loss, and the family history mentions a different disorder. Ground observed and excluded HPO terms first, then rank a differential without treating the probabilities as a confirmed diagnosis.
