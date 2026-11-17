---
description: Selects query-retigene-papers-with-aiscientist-mcp for a request it should handle.
tags: [trigger, literature]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

What are the haploinsufficient genes in the RetiGene papers? I need one row per gene with the sentence that says it, the PMID and the page, and the hedged ones kept apart. We have the RetiGene index on the cluster and an Anthropic key.
