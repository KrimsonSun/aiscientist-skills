"""Tests of scripts/vkb_client.py against a fake API that trims pages like visionkb-api 0.1.x.

Standard library only: the fake `fetch` stands in for HTTP, so httpx is not needed.
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "vkb_client.py"
spec = importlib.util.spec_from_file_location("vkb_client", SCRIPT)
vkb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vkb)

ROWS = [{"group_label": f"G{i}", "pseudobulk_cp10k": 100 - i} for i in range(10)]
SRS = [{"id": f"visionkb:sr-{i}", "pmid": f"PMID:{1000 + i}"} for i in range(7)]
CAP = 3  # the fake API returns at most 3 items per response, whatever the limit


def envelope(data, page, warnings=()):
    return {
        "status": "ok",
        "kg_release": "visionkb-0000.01.0",
        "data": data,
        "page": page,
        "warnings": list(warnings),
        "error": None,
    }


def trimmed(items, offset, limit, name):
    """A page of items[offset:offset+limit], cut to CAP items with the API's warning."""
    page = items[offset : offset + limit]
    if len(page) <= CAP:
        return page, []
    msg = f"{name}: returned {CAP} of {len(page)} items to stay within 24000 characters; page with limit/offset"
    return page[:CAP], [msg]


def fake_api(calls):
    def fetch(path, params):
        calls.append((path, dict(params)))
        offset, limit = params.get("offset", 0), params.get("limit", 50)
        if path == "/atlas/expression":
            data, warns = trimmed(ROWS, offset, limit, "data")
            return 200, envelope(
                data, {"limit": limit, "offset": offset, "total": len(ROWS)}, warns
            )
        if path.startswith("/evidence/"):
            srs, warns = trimmed(SRS, offset, limit, "data.study_results")
            data = {"edge": {"edge_id": path.rsplit("/", 1)[1]}, "study_results": srs}
            return 200, envelope(data, {"limit": limit, "offset": offset, "total": len(SRS)}, warns)
        if path == "/entities/search":
            hits = [
                {"id": "HGNC:6685", "symbol": "LRAT", "match": "exact_symbol"},
                {"id": "HGNC:20743", "symbol": "LRATD1", "match": "fulltext"},
            ]
            return 200, envelope(hits, {"limit": limit, "offset": 0, "total": None})
        err = {"code": "missing_anchor", "message": "give subject or object (or both)"}
        return 400, {**envelope(None, None), "status": "error", "error": err}

    return fetch


def test_get_all_reads_every_row_of_trimmed_pages():
    calls = []
    kg = vkb.KG(fetch=fake_api(calls))
    env = kg.get_all("/atlas/expression", genes="LRAT", limit=5)
    assert [r["group_label"] for r in env["data"]] == [r["group_label"] for r in ROWS]
    assert [c[1]["offset"] for c in calls] == [0, 3, 6, 9]  # advanced by rows received
    assert env["page"]["returned"] == env["page"]["total"] == 10
    assert vkb.coverage(env) == "complete: 10 of 10"


def test_paging_by_limit_would_skip_rows():
    """The bug this client avoids: offset += limit drops the rows the API trimmed away."""
    fetch, seen, offset = fake_api([]), [], 0
    while offset < len(ROWS):
        _, env = fetch("/atlas/expression", {"limit": 5, "offset": offset})
        seen += [r["group_label"] for r in env["data"]]
        offset += 5
    assert len(seen) == 6 and "G3" not in seen


def test_coverage_of_one_trimmed_page():
    kg = vkb.KG(fetch=fake_api([]))
    env = kg.get("/atlas/expression", genes="LRAT", limit=5)
    assert len(env["data"]) == 3
    assert vkb.coverage(env) == "trimmed: 3 of 10 (character cap; page on with offset=3)"


def test_coverage_partial_and_ranked():
    kg = vkb.KG(fetch=fake_api([]))
    assert vkb.coverage(kg.get("/atlas/expression", limit=2)) == (
        "partial: 2 of 10 (limit; page on with offset=2)"
    )
    assert (
        vkb.coverage(kg.get("/entities/search", q="LRAT")) == "top 2 (ranked; total not reported)"
    )


def test_evidence_all_pages_study_results():
    calls = []
    kg = vkb.KG(fetch=fake_api(calls))
    env = kg.evidence_all("visionkb:e-" + "0" * 40, limit=200)
    assert [s["id"] for s in env["data"]["study_results"]] == [s["id"] for s in SRS]
    assert [c[1]["offset"] for c in calls] == [0, 3, 6]
    assert not env["warnings"]
    single = kg.get("/evidence/visionkb:e-" + "0" * 40, limit=200)
    assert vkb.coverage(single, single["data"]["study_results"]).startswith("trimmed: 3 of 7")


def test_resolve_and_errors():
    kg = vkb.KG(fetch=fake_api([]))
    gene, _ = kg.resolve("LRAT")
    assert gene == "HGNC:6685"
    with pytest.raises(RuntimeError, match="missing_anchor"):
        kg.get("/relationships", predicate="biolink:expressed_in")
