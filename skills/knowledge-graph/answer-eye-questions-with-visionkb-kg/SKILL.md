---
name: answer-eye-questions-with-visionkb-kg
description: Answer chat-style knowledge questions about eye genes, cell types, diseases and datasets from the VisionKB knowledge graph through its read-only HTTP API or the equivalent visionkb-kg MCP tools, citing the KG release and dataset versions. Resolves a gene or cell type to a CURIE, reads per-class and per-cell-type expression from the HECA atlas summaries, reads typed Biolink relationships with knowledge_level, sources and PMIDs, opens the evidence behind an edge, and finds atlases with ready bind records, keeping atlas observations apart from curated claims. Use for questions such as which retinal cell types express LRAT, which class has the highest RHO, which diseases and PMIDs are recorded for PRPF31, or which atlases contain RPE cells. Not for new analysis of cell-level data.
license: MIT
compatibility: Needs network access to a running VisionKB API (visionkb-api 0.1.1 or later, deployed with visionkb-deploy) and a read token in a file; Python 3.11+ with httpx (scripts/vkb_client.py), or curl and jq. No local compute, no atlas files, no scheduler.
metadata:
  category: knowledge-graph
  version: "0.0.1"
  status: community
  author: "Jin Li"
  tags: "knowledge-graph, biolink, gene-expression, retina, eye, cell-atlas, disease-genes, provenance, rest-api, mcp"
  tested-with: "visionkb-api 0.1.1 (image digest sha256:5d956d03...), visionkb-deploy 0.1.1, KG release visionkb-2026.11.0, Neo4j 2026.10.1 Community, PostgreSQL 17.11, httpx 0.28.1, Python 3.13.18, curl 8.23.0, jq 1.8.2"
  compute: "none on the client: the four worked questions (roughly 100 HTTP requests, most of them evidence lookups) took 8-18 s wall (four runs) against a stack on the same node; the server stack used 4 GB Neo4j heap and 8 GB page cache"
  requires-gpu: "false"
  scheduler: "none"
  requires-network: "runtime"
  requires-secrets: "VISIONKB_API_TOKEN_FILE"
---

# Answer eye knowledge questions with the VisionKB knowledge graph

VisionKB is a Biolink 4.4.6 knowledge graph of eye biology: HGNC genes, Cell Ontology cell types
plus dataset-specific cell states, UBERON tissues, MONDO diseases, HPO phenotypes, the 13 Human
Eye Cell Atlas (HECA) single-cell and single-nucleus atlases as datasets, expression edges derived
from those atlases, and curated gene-disease claims. It is served read-only by
[visionkb-api](https://github.com/lijinbio/visionkb-api) (deployment:
[visionkb-deploy](https://github.com/lijinbio/visionkb-deploy)) and released as immutable,
versioned bundles (`kg_release` = `visionkb-YYYY.MM.N`).

This skill is the **knowledge answer** route: a few API calls (seconds), no atlas files opened, no
jobs. Every response carries `kg_release`; every expression row carries `dataset_id` and
`dataset_version`. Cite both.

Tested end to end, as written, against a stack deployed with visionkb-deploy 0.1.1 on an HPC
compute node, serving the first real release `visionkb-2026.11.0` (Biolink 4.4.6; 2,783,649 nodes; 2,359,657 `expressed_in` edges with
2,758,076 StudyResults from the 13 HECA atlases at `heca-2026.05`; 22 curated gene-disease or
gene-phenotype edges). The outputs quoted below are from that run; the HECA datasets are
`access_level: lab`, so only the values needed to read the example are shown, rounded.

Replace every `/path/to/...` with your own values.

## When to use

- "Which cell types / major classes express gene X, how strongly, with how many donors?"
- "Which class has the highest X?" (ranked atlas summaries).
- "What is known about gene X and disease Y, with PMIDs?" (curated `causes` / `gene_associated_with_condition`).
- "Which genes are associated with disease Y?", "Which genes are expressed in cell type Z?" (gene sets).
- "Which atlases contain RPE cells / are from retina, and how do I attach one?" (registry + bind record).
- Before an analysis of a bound atlas: pick the dataset and the prior evidence to compare against.

## When NOT to use

- New statistics on cell-level data (DE, composition, signature scoring, donor-aware tests): bind
  the atlas the registry returns and run the analysis tools; the KG holds summaries only.
- Region-specific claims from the graph: region x class numbers exist only in the atlas summary
  table (`level=region_majorclass`), never as edges.
- Perturbation results and cell-state comparisons: not in the 0.1 API (not exposed).

## 1. Environment

```bash
mamba create -y -n visionkb_kgclient -c conda-forge python=3.13 httpx=0.28.1 jq curl
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate visionkb_kgclient
export VISIONKB_API_URL=http://127.0.0.1:8770/v1                 # your deployment
export VISIONKB_API_TOKEN_FILE=/path/to/secrets/api_token_read   # one line: the read token
export VKB_SKILL_SCRIPTS=/path/to/answer-eye-questions-with-visionkb-kg/scripts   # vkb_client.py
```

The tested solve: Python 3.13.18, httpx 0.28.1, curl 8.23.0, jq 1.8.2 (conda-forge). With visionkb-deploy, `bin/visionkb init` writes the read
token to `<deploy dir>/<instance>/secrets/api_token_read` (mode 600) and `bin/visionkb health`
checks the stack. Never paste the token into code, logs or reports.

## 2. Client

Every call returns the same envelope:
`{"status": "ok"|"error", "kg_release", "data", "page": {"limit", "offset", "total"} | null, "warnings", "error"}`.
Lists default to 50 rows (max 200). Errors are returned as envelopes, never as invented data.

**A page can hold fewer rows than `limit`.** The API trims every response to stay under about
24,000 characters and then warns `<list>: returned N of M items to stay within 24000 characters;
page with limit/offset`. Advance `offset` by the number of rows received (`len(data)`), never by
`limit`, or the trimmed rows are skipped silently. [scripts/vkb_client.py](scripts/vkb_client.py)
(httpx; its paging logic is tested in `tests/` against a fake API that trims every page) does
this:

| Function | Does |
| --- | --- |
| `KG(url, token_file)` | client with the bearer token read from the file |
| `kg.get(path, **params)` | one call; raises on `status: error`, prints `warnings` |
| `kg.get_all(path, **params)` | every row of a list endpoint, `offset += len(data)` until `page.total` |
| `kg.evidence_all(edge_id)` | `/evidence/{edge_id}` with every StudyResult, paged the same way |
| `kg.resolve(q, category)` | `search_entities`, exact CURIE or symbol match only, else `LookupError` |
| `coverage(env[, rows])` | `complete: n of total`, `trimmed: n of total (...)`, `partial: ...` or `top n` (search) |

Use `get_all` / `evidence_all` for anything you count or conclude from; when you keep a single
page (a top-5 view), print `coverage(...)` with it so the answer says what it covers. The worked
questions start with:

```python
import json
import os
import pathlib
import sys

sys.path.insert(0, os.environ["VKB_SKILL_SCRIPTS"])  # <skill folder>/scripts
from vkb_client import KG, coverage

kg = KG(os.environ["VISIONKB_API_URL"], os.environ["VISIONKB_API_TOKEN_FILE"])
get, get_all, resolve = kg.get, kg.get_all, kg.resolve
OUT = pathlib.Path(sys.argv[1])  # every response envelope is kept here, for the report
OUT.mkdir(parents=True, exist_ok=True)
SEQ = [0]


def save(name, env):
    SEQ[0] += 1
    (OUT / f"{SEQ[0]:02d}_{name}.json").write_text(json.dumps(env, indent=1))


def show(rows, cols):
    for r in rows:
        print("  " + "  ".join(f"{c}={r.get(c)}" for c in cols))
```

The same calls with curl and jq (these ran as written):

```bash
H="Authorization: Bearer $(cat "$VISIONKB_API_TOKEN_FILE")"
curl -fsS "$VISIONKB_API_URL/ready" >ready.json
curl -fsS -H "$H" "$VISIONKB_API_URL/entities/search?q=LRAT&category=biolink:Gene&limit=3" >search.json
curl -fsS -H "$H" "$VISIONKB_API_URL/atlas/expression?genes=LRAT&level=majorclass&limit=3" >atlas.json
jq -c '{kg_release, ready: .data}' ready.json
jq -c '.kg_release, (.data[] | {id, symbol, match})' search.json
jq -c '.data[] | {dataset_id, dataset_version, group_label, pct_expressing, pseudobulk_cp10k}' atlas.json
# one page only: say how much of the result it is (rows < limit can mean trimmed, see warnings)
jq -c '{returned: (.data | length), page, warnings}' atlas.json
# errors are envelopes too: no token -> 401; no anchor -> missing_anchor; absent predicate
curl -sS -o /dev/null -w 'no token: HTTP %{http_code}\n' "$VISIONKB_API_URL/release"
curl -sS -H "$H" "$VISIONKB_API_URL/relationships?predicate=biolink:expressed_in" | jq -c '{status, error}'
curl -sS -H "$H" "$VISIONKB_API_URL/relationships?subject=HGNC:6685&predicate=biolink:treats" | jq -c '.error'
```

What came back: `ready` with `neo4j`, `summaries` and `postgres` all `ok` and the release id;
`LRAT` resolved to `HGNC:6685` (`exact_symbol`) with `LRATD1` and `LRATD2` as `fulltext` hits; the
top three LRAT rows across all atlases were RPE groups of `ds-rpechoroid-scrna`, `ds-hrca-snrna`
and `ds-rpechoroid-snrna`; no token gave HTTP 401; `/relationships` without an anchor gave
`missing_anchor`.

The `{returned, page, warnings}` line is the same check for one curl page; here it gave
`returned: 3` with `limit: 3`, `total: 132` and no warning, i.e. a partial page by `limit`, not a
trimmed one.

## 3. What is in the graph, and what each field means

| Source | Edges | `knowledge_level` | `agent_type` | `primary_knowledge_source` |
| --- | --- | --- | --- | --- |
| HECA atlas summaries | `expressed_in` (gene -> cell type or state) | `observation` | `data_analysis_pipeline` | `infores:visionkb-heca` |
| RetiGene curated haploinsufficiency review | `causes`, `gene_associated_with_condition` (gene -> disease), `has_phenotype` (gene -> HPO) | `knowledge_assertion` | `manual_validation_of_automated_agent` | `infores:visionkb-retigene` |
| CL, UBERON, MONDO, HPO | `subclass_of`, `part_of` | `knowledge_assertion` | `manual_agent` | `infores:cl`, ... |

`knowledge_level` is what keeps observations apart from claims: an `expressed_in` edge says "this
transcript was measured in these cells of this atlas", nothing about function; a
`causes` or `gene_associated_with_condition` edge is a curated statement backed by publications
(with a curator `grade` per StudyResult). Filter with
`knowledge_level=` on `/relationships` and report the two kinds in separate paragraphs.

**Evidence.** Each edge lists `has_study_results`; `GET /evidence/{edge_id}` returns them. For
expression, one StudyResult per (dataset, level, group) with `n_cells`, `n_donors`,
`pct_expressing`, `mean_log1p_cp10k`, `pseudobulk_cp10k`, `n_donors_expressing`, `method`; for
curated claims, `pmid`, `page`, `evidence_kind`, `grade` and a short `supporting_text` (lab
curation: do not quote it outside the lab).

**What makes an `expressed_in` edge (VisionKB decision D18).** A (gene, dataset, group) becomes an
edge, with a StudyResult, only if all of these hold:

1. `pct_expressing >= 0.10` and `n_cells >= 20` in the group;
2. `pseudobulk_cp10k >= 0.10 x` the gene's maximum over the groups of the same dataset and level
   (specificity: removes low-level spill-over of very abundant transcripts);
3. `n_donors_expressing >= 2` (a donor counts when >= 10 % of its cells in the group express the
   gene). Atlases without donor labels would use 1-2 only, with flagged edges; all 13 atlases of
   `visionkb-2026.11.0` have donor labels.

Edges exist at two levels, `majorclass` and `celltype` (CL class, or a `visionkb:cs-<dataset>-<label>`
CellState that is `subclass_of` a CL class). **Region x major class numbers are only in the
Parquet summaries** (`/atlas/expression?level=region_majorclass`); there are no regional edges.

**Absence of an edge is not evidence of non-expression.** The graph keeps only the rows that pass
the rule above. Before saying "X is not expressed in Z", read the atlas rows
(`/atlas/expression`, all genes x groups, no threshold) and report `pct_expressing`,
`pseudobulk_cp10k` and donor support. Also check that the gene and group exist in that dataset:
a gene missing from the summaries comes back as no rows plus the warning
`<gene>: not found in the expression summaries`, not as zeros.

**Ambient RNA in snRNA.** Very abundant transcripts leak into other nuclei. In the HRCA snRNA
atlas, RHO is detected in 17-28 % of amacrine, bipolar, cone and Müller-glia nuclei at 3-9 % of
the rod pseudobulk (section 4.2). Rule 2 removes those edges, but the atlas rows still show
them: a rod gene at 0.1-0.3 `pct_expressing` in a non-rod class is contamination until shown
otherwise (for example by specific expression in an scRNA atlas or by another method). Say so
whenever you report such a row.

**Doublet programs in small subtypes (known issue KI-1).** Small subtypes of one class can carry
the program of another, abundant class (rod genes in amacrine subtypes in `visionkb-2026.11.0`).
Those groups pass all three rules and get edges. For a gene that marks one major class strongly,
read the major-class rows first and treat edges to small subtypes of a different class as
possible contamination (section 4.2 shows how to check every edge).

## 4. A knowledge answer (Route A) in about six calls

1. `GET /release`: `kg_release`, atlases and versions, predicates present.
2. `GET /entities/search?q=...`: exact CURIE / symbol match only (synonym or full-text hits need
   checking).
3. `GET /atlas/expression?genes=...&level=majorclass|celltype` (add `dataset=` to stay in one atlas).
4. `GET /relationships?subject=<CURIE>&predicate=...` (or `knowledge_level=`).
5. `GET /evidence/{edge_id}` for the edges you cite.
6. `GET /datasets?entities=...|tissue=...` when the next step is an analysis.

The parameters of the worked questions below:

```python
Q1_GENE = os.environ.get("Q1_GENE", "LRAT")
Q1_DATASET = os.environ.get("Q1_DATASET", "visionkb:ds-hrca-snrna")
Q2_GENE = os.environ.get("Q2_GENE", "RHO")
Q3_GENE = os.environ.get("Q3_GENE", "PRPF31")
```

### 4.0 Which release am I querying?

```python
rel = get("/release")
save("release", rel)
print("kg_release:", rel["kg_release"], "| biolink", rel["data"]["biolink_version"])
print("predicates:", rel["data"].get("predicates_in_graph"))
print("edges by predicate:", rel["data"]["counts"]["edges_by_predicate"])
for a in rel["data"]["atlases"]:
    print("  atlas", a["dataset_id"], a["atlas_version"])
expect = os.environ.get("VISIONKB_EXPECT_RELEASE")
assert expect is None or rel["kg_release"] == expect, (rel["kg_release"], expect)
```

The run printed `visionkb-2026.11.0`, the six predicates present (`causes`, `expressed_in`,
`gene_associated_with_condition`, `has_phenotype`, `part_of`, `subclass_of`), the edge counts per
predicate and the 13 atlases, all at `heca-2026.05`.

**Known issues are not in `/release`.** visionkb-api 0.1.1 does not return the manifest's
`known_issues`; read `validation/known_issues.json` (or the Known issues section of
`validation/report.md`) of the release bundle, or ask the operator. For `visionkb-2026.11.0` it
holds KI-1 (section 3).

### 4.1 In which classes and cell types is LRAT expressed? (expression, observation)

```python
print(f"\n# Q1 {Q1_GENE}: expression by class and cell type")
gene, hits = resolve(Q1_GENE)
save("q1_search", hits)
print("  search:", coverage(hits))
show(hits["data"], ["id", "symbol", "name", "match"])

edges = get_all("/relationships", subject=gene, predicate="biolink:expressed_in", limit=200)
save("q1_expressed_in_edges", edges)
print("  expressed_in edges (all atlases):", coverage(edges))
for e in edges["data"][:8]:
    print("   ", e["object"]["id"], e["object"]["name"], e["qualifiers"], e["summary"])
# an edge aggregates atlases: its StudyResults say which (dataset, level, group) support it
edge_groups = set()
for e in edges["data"]:
    for sr in kg.evidence_all(e["edge_id"], limit=200)["data"]["study_results"]:
        edge_groups.add((sr["dataset_id"], sr["level"], sr["group_label"]))

for level in ("majorclass", "celltype"):
    ex = get_all("/atlas/expression", genes=gene, dataset=Q1_DATASET, level=level, limit=200)
    save(f"q1_atlas_{level}", ex)
    top_cp10k = ex["data"][0]["pseudobulk_cp10k"]  # rows are sorted by pseudobulk_cp10k
    print(f"  atlas {level}:", coverage(ex), "| rule a/b/c as in D18")
    for r in ex["data"][:5]:
        a = r["pct_expressing"] >= 0.10 and r["n_cells"] >= 20
        b = r["pseudobulk_cp10k"] >= 0.10 * top_cp10k
        c = r["n_donors_expressing"] >= 2
        print(
            f"   {r['group_label']} {r['cell_type_id']} n_cells={r['n_cells']} "
            f"pct={r['pct_expressing']} cp10k={r['pseudobulk_cp10k']} "
            f"donors={r['n_donors_expressing']}/{r['n_donors']} a={a} b={b} c={c} "
            f"edge={(Q1_DATASET, level, r['group_label']) in edge_groups}"
        )

reg = get("/atlas/expression", genes=gene, dataset=Q1_DATASET, level="region_majorclass", limit=5)
save("q1_atlas_region_majorclass", reg)
print("  atlas region_majorclass (Parquet only, no KG edges):", coverage(reg))
show(reg["data"], ["group_label", "region", "pct_expressing", "pseudobulk_cp10k"])

if edges["data"]:
    ev = get(f"/evidence/{edges['data'][0]['edge_id']}", limit=10)  # first page only
    save("q1_evidence_top_edge", ev)
    srs = ev["data"]["study_results"]
    print("  evidence:", ev["data"]["edge"]["object"]["id"], coverage(ev, srs))
    cols = ["dataset_id", "atlas_version", "level", "group_label", "n_donors_expressing", "method"]
    show(srs, cols)
```

What the run showed (HRCA snRNA, 3,177,310 nuclei, `heca-2026.05`):

- `LRAT` -> `HGNC:6685` (`exact_symbol`). 28 `expressed_in` edges over all atlases: RPE (CL and
  dataset-specific RPE states), melanocytes, Schwann cells and one reactive Müller-glia state
  (`MG_reactive`). Edges
  to the same cell type with different `anatomical_context_qualifier` (retina vs RPE/choroid) are
  separate edges.
- Major class: RPE is the top group (about three quarters of nuclei, 23 of 24 donors); it passes
  rules a, b and c and has an edge. Müller glia come second at about 7 % of nuclei and 4 % of the
  RPE pseudobulk, with 21 of 100 donors: rules a and b fail, so **no edge, but the gene is
  detected**. Report it as low-level detection, not as absence.
- Cell type: amacrine subtype HAC39 has about 24 % of nuclei expressing and 73 donors, so it
  passes a and c, but fails b (under 10 % of the RPE pseudobulk): no edge.
- Region x major class: 30 rows (the code keeps the top 5 and says `partial: 5 of 30`), only in the Parquet (RPE pseudobulk is similar in fovea, macula and
  periphery). There are no regional edges to query.
- The evidence of the top RPE edge lists three StudyResults, each with dataset, atlas version,
  level, group and the D18 `method` string.

### 4.2 Which major class shows the highest RHO? (ranking, ambient RNA)

```python
print(f"\n# Q2 {Q2_GENE}: top major class per atlas, then every edge checked against it")
rho, _ = resolve(Q2_GENE)
top = get_all("/atlas/expression", genes=rho, level="majorclass", limit=200)
save("q2_atlas_majorclass_all_datasets", top)
by_ds = {}
for r in top["data"]:  # sorted by pseudobulk_cp10k over all atlases
    by_ds.setdefault(r["dataset_id"], []).append(r)
top_class = {ds: rows[0]["cell_type_id"] for ds, rows in by_ds.items()}
for ds, rows in by_ds.items():
    detected = [r["group_label"] for r in rows if r["pct_expressing"] >= 0.10]
    print(f"  {ds}: top {rows[0]['group_label']}; groups with pct>=0.10: {detected}")
    show(rows[:3], ["group_label", "n_cells", "pct_expressing", "pseudobulk_cp10k"])

# Majorclass first, then each edge's StudyResults: support from a group of ANOTHER class than the
# atlas's top class (a small subtype, or a non-rod class in snRNA) is possible contamination
# (doublets or ambient RNA), not expression. Known issue KI-1 of visionkb-2026.11.0.
rho_edges = get_all("/relationships", subject=rho, predicate="biolink:expressed_in", limit=200)
save("q2_expressed_in_edges", rho_edges)
print(f"  expressed_in edges for {Q2_GENE}:", coverage(rho_edges))
for e in rho_edges["data"]:
    o = e["object"]["id"]
    parents = get_all("/relationships", subject=o, predicate="biolink:subclass_of", limit=50)[
        "data"
    ]
    parent_ids = [x["object"]["id"] for x in parents]
    for sr in kg.evidence_all(e["edge_id"], limit=200)["data"]["study_results"]:
        tc = top_class[sr["dataset_id"]]
        flag = "" if tc in (o, *parent_ids) else "  <- not the top class: check"
        print(
            f"   {o} ({e['object']['name']}) parent={parent_ids} | {sr['dataset_id']} "
            f"{sr['level']} "
            f"{sr['group_label']} n_cells={sr['n_cells']} pct={sr['pct_expressing']} "
            f"cp10k={sr['pseudobulk_cp10k']} donors={sr['n_donors_expressing']}{flag}"
        )
```

What the run showed:

- Major class: Rod is the top class in both HRCA atlases (snRNA: about 91 % of 1,066,056 rod
  nuclei, 103 donors). In HRCA snRNA, RHO is also detected in at least 10 % of nuclei of **every**
  other major class (AC 17 %, BC, Cone and MG 26-28 %) at 3-9 % of the rod pseudobulk, which is
  the ambient-RNA signature; rule b removes those major-class edges. Microglia, astrocyte and RPE
  sit just above the threshold (10-12 % of the rod level) and keep edges: treat them as
  unresolved (ambient RNA, or phagocytosed outer segments) unless another atlas or method
  supports them.
- 20 edges in total. Besides Rod: 14 amacrine subtypes of HRCA snRNA (39 to 1,057 nuclei each)
  with 40-84 % of nuclei expressing at 11-28 % of the rod pseudobulk, and the bipolar type OFFx.
  Twelve of those subtypes plus SEG* are exactly the 13 rod-program groups of **KI-1**; VG3* and
  OFFx are not listed there but follow the same pattern.
- ONONH snRNA has no rods; its top class for RHO is MG at about 10 % of nuclei and 0.3 CP10k, so
  the within-atlas rule keeps an edge there. Compare with the gene's home class in other atlases
  (15.8 CP10k in HRCA snRNA rods) before calling it expression.

**Known issue KI-1 of `visionkb-2026.11.0` (decision D19).** Several small HRCA snRNA amacrine
subtypes (for example HAC79, HAC82, HAC89, AII*) carry a rod transcript program (KI-1 median
ratios to the rod level 0.14-0.25 for those four, with PDE6A, SAG, CNGB1 and PDE6G as examples;
RHO at 11-28 % of the rod level in the run above), most likely rod-amacrine doublets. Their
`expressed_in` edges to rod genes are real rows of the summaries but probably not expression.
For photoreceptor genes, and generally any gene that is a strong marker of another major class:
read the major-class rows first, then treat edges to small subtypes of a different class as
possible contamination and cite KI-1. No edge is flagged or removed in this release; a
contamination QC flag is planned for `visionkb-2026.11.1`.

### 4.3 Which diseases are associated with PRPF31, with PMIDs? (curated claims)

```python
print(f"\n# Q3 {Q3_GENE}: disease edges (curated claims) and their evidence")
g3, _ = resolve(Q3_GENE)
allrel = get_all("/relationships", subject=g3, limit=200)
save("q3_all_edges", allrel)
levels = {}
for e in allrel["data"]:
    k = (e["predicate"], e["knowledge_level"], e["primary_knowledge_source"])
    levels[k] = levels.get(k, 0) + 1
for k, n in sorted(levels.items()):
    print("  ", *k, n)
dis = get_all("/relationships", subject=g3, object_category="biolink:Disease", limit=50)
save("q3_disease_edges", dis)
print("  edges to diseases:", coverage(dis))
for e in dis["data"]:
    o = e["object"]
    print("   ", e["predicate"], o["id"], o["name"], e["knowledge_level"], e["agent_type"])
    pubs = e["publications"]  # at most 5 here; n_publications is the full count
    print("     ", e["primary_knowledge_source"], pubs, f"({len(pubs)} of {e['n_publications']})")
if dis["data"]:
    ev3 = kg.evidence_all(dis["data"][0]["edge_id"], limit=200)
    save("q3_evidence", ev3)
    print("  evidence:", coverage(ev3, ev3["data"]["study_results"]))
    print("  publications:", ev3["data"]["publications"])
    show(ev3["data"]["study_results"], ["id", "pmid", "grade"])
    gs = get_all(
        "/gene-sets", entity=dis["data"][0]["object"]["id"], kind="disease_genes", limit=50
    )
    save("q3_gene_set_disease", gs)
    print(f"  genes associated with {dis['data'][0]['object']['id']}:", coverage(gs))
    show(gs["data"], ["gene_id", "symbol", "score"])
```

What the run showed:

- 201 edges from `PRPF31` (`HGNC:15446`): 200 `expressed_in` (observation, `infores:visionkb-heca`)
  and 1 curated claim.
- The claim is `biolink:causes` -> `MONDO:0019200` retinitis pigmentosa, `knowledge_assertion`,
  `manual_validation_of_automated_agent`, `infores:visionkb-retigene`. The edge lists 5 PMIDs (the
  relationship view is capped at 5); its evidence has 12 StudyResults with 8 distinct PMIDs
  (`PMID:12714658`, `18450588`, `20232351`, `24419317`, `33576794`, `36672815`, `37809982`,
  `40674075`), each with the curator `grade`.
- `/gene-sets` for retinitis pigmentosa returned 3 genes (PRPF31, PRPF4, RP1).

The curated claims come from one source, a haploinsufficiency review: 22 gene-disease or
gene-phenotype edges in this release (`causes`, `gene_associated_with_condition`,
`has_phenotype`). **A missing disease edge says nothing about the gene**; say "not in the curated
source of this release". Use `object_category=biolink:Disease` (or `biolink:PhenotypicFeature`
for HPO) rather than one predicate, since the curated predicates differ by claim.

### 4.4 Which atlases can I attach for RPE, or for retina? (datasets, bind records)

```python
print("\n# Q4 datasets with bind records")
rpe = get("/entities/search", q="retinal pigment epithelial cell", category="biolink:Cell", limit=3)
save("q4_search_rpe", rpe)
print("  search:", coverage(rpe))
show(rpe["data"], ["id", "name", "match"])
rpe_id = next(h["id"] for h in rpe["data"] if h["name"] == "retinal pigment epithelial cell")
for label, params in (
    ("rpe_cells", {"entities": rpe_id}),
    ("retina", {"tissue": "UBERON:0000966"}),
):
    ds = get_all("/datasets", limit=50, **params)
    save(f"q4_datasets_{label}", ds)
    print(f"  {label} datasets:", coverage(ds))
    for d in ds["data"]:
        bind = {k: v for k, v in d["bind"].items() if k != "path"}  # path = HPC-side h5ad path
        print("   ", d["id"], d["version"], d["assay"], d["n_cells"], d["access_level"], bind)

print("\ndone:", SEQ[0], "responses saved in", OUT)
```

What the run showed:

- `retinal pigment epithelial cell` resolved by full text to `CL:0002586` (checked by name).
- 5 datasets have RPE cells: HRCA scRNA and snRNA, ONONH snRNA, RPE/choroid scRNA and snRNA
  (`matched` says why; for the last three it also lists the dataset-specific RPE cell states
  under `via`). All are
  `heca-2026.05`, `access_level: lab`.
- `tissue=UBERON:0000966` (retina) returned the two HRCA atlases.
- Each record carries `bind = {name, path, role: "reference"}`. `path` is the HPC-side `.h5ad`
  path for an analysis job (AiScientist attaches it); the API never opens it, and the code above
  leaves it out of the printout. Never publish it.

## 5. The same with the MCP server

The `visionkb-kg` MCP server (from [aiscientist-mcp](https://github.com/lijinbio/aiscientist-mcp))
has one tool per endpoint, with the query parameters as arguments (names as specified for the
server): `get_release`,
`search_entities`, `get_relationships`, `get_evidence`, `get_gene_set`, `query_atlas_expression`,
`find_datasets`. The mapping is in [references/mcp-tools.md](references/mcp-tools.md). This
skill's runs used the HTTP API only.

## 6. Validate before answering

1. **Release.** Every envelope has the same `kg_release` as `/release`. Mixing releases in one
   answer is an error.
2. **Resolution.** `match` is `exact_id` or `exact_symbol`. A `synonym` or `fulltext` hit must be
   checked by name; HGNC previous symbols and aliases are synonyms here.
3. **Warnings.** Read them: "not found in the expression summaries", "matches N genes",
   deprecated predicates, and lower-than-graph thresholds all arrive as warnings.
4. **Paging.** `page.total` larger than the rows you read means you have not seen everything
   (search returns ranked top-k with `total: null`).
5. **Donor support.** A high `pct_expressing` with `n_donors_expressing` of 0-1 is weak; say so.
6. **Ambient RNA, doublets and absence.** As in section 3: no edge does not mean no expression;
   abundant transcripts in snRNA leak into other classes; edges to small subtypes of another
   class may be doublet programs. Check the release's known issues (KI-1 in `visionkb-2026.11.0`).
7. **Access level.** HECA datasets are `access_level: lab` until published; do not send their rows
   outside the lab.

## 7. Report

- `kg_release`, and for every expression number the `dataset_id` and `dataset_version`;
- each entity with its CURIE and how it was resolved;
- expression (observation) and curated claims (knowledge_assertion) in separate paragraphs, each
  claim with `primary_knowledge_source` and PMIDs;
- for expression: level, group, `pct_expressing`, `pseudobulk_cp10k`, `n_donors_expressing` /
  `n_donors`; the ambient-RNA, doublet (known issue id) and absence caveats where they apply;
- for datasets: id, version, assay, cell count, `access_level` and the `bind` record;
- what was not checked (e.g. other atlases, other levels, pages not read).

## Troubleshooting

HTTP 401, `missing_anchor`, truncated lists, a proxy setting that breaks httpx, and a Neo4j store
that loads fewer nodes than the manifest: see [references/troubleshooting.md](references/troubleshooting.md).
