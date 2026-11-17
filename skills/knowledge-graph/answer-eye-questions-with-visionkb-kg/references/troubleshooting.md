# Troubleshooting

Every row except the last was observed in this skill's runs on `visionkb-2026.11.0`; the 503
readiness row comes from the visionkb-deploy smoke tests.

| Symptom | Cause | Fix |
| --- | --- | --- |
| HTTP 401 | missing or wrong bearer token | check `VISIONKB_API_TOKEN_FILE` |
| 400 `missing_anchor` | `/relationships` without `subject` or `object` | anchor on a CURIE |
| 400 `predicate_not_in_release` | predicate not used in this release | read `predicates_in_graph` from `/release` |
| `httpx.InvalidURL: Invalid port: ':1]'` | a `[::1]` entry in `NO_PROXY` (httpx 0.28.1) | remove that entry for the client process |
| fewer rows than `limit`, warning `returned N of M items` | 24,000-character cap per response | advance `offset` by `len(data)`, not by `limit` (`kg.get_all`, `kg.evidence_all`) |
| `load-release` warns that loaded node counts differ from the manifest | Neo4j store on a parallel filesystem (seen with this release) | put `VISIONKB_DEPLOY_DIR` on node-local disk and reload |
| 503 on `/v1/ready` | Neo4j, summaries or PostgreSQL down | `bin/visionkb health` on the server |
