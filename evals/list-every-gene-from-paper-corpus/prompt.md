---
description: Selects read-whole-corpus-with-claude for a request it should handle.
tags: [trigger, literature]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Our lab has about 1,700 full-text papers on inherited retinal disease, already split into passages in a chunks.jsonl file for our RAG. The PI wants every gene these papers report as causing disease through haploinsufficiency, with the supporting quotes. Our RAG answer only cites a dozen papers and I'm sure it misses genes. How do I get a list that is actually complete, and roughly what would it cost?
