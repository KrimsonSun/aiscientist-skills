# MCP tools and HTTP endpoints

The `visionkb-kg` MCP server (from [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp))
wraps the same endpoints, one tool each; the arguments are the HTTP query parameters used in
SKILL.md. The tool names are those specified for the server; this skill's tested runs used the
HTTP API only, not the MCP server.

| MCP tool | HTTP endpoint | Use |
| --- | --- | --- |
| `get_release` | `GET /v1/release` | release id, atlases, counts, predicates |
| `search_entities` | `GET /v1/entities/search` | name, symbol, synonym or CURIE to CURIE |
| `get_relationships` | `GET /v1/relationships` | typed edges from or to an entity |
| `get_evidence` | `GET /v1/evidence/{edge_id}` | StudyResults and publications of one edge |
| `get_gene_set` | `GET /v1/gene-sets` | genes expressed in a cell type, or genes of a disease |
| `query_atlas_expression` | `GET /v1/atlas/expression` | atlas summary rows, no threshold |
| `find_datasets` | `GET /v1/datasets` | registry records with bind records |
