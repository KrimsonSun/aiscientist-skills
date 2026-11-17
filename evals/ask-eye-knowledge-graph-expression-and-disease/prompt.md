---
description: Selects answer-eye-questions-with-visionkb-kg for a request it should handle.
tags: [trigger, knowledge-graph]
runs: 3
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Our lab runs the eye knowledge graph service (the VisionKB API on the cluster; I have a read token). Quick chat answer, no new analysis: which retinal major classes and cell types express LRAT, what disease associations are recorded for PRPF31 and with which PMIDs, and which atlases with RPE cells I could attach for a follow-up. Keep the atlas observations apart from the curated claims, and give me the release ID so I can cite it.
