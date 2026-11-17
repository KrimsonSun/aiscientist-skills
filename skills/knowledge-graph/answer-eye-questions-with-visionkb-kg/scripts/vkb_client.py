"""Minimal client of the read-only VisionKB API (visionkb-api >= 0.1.1), used by the skill.

The API trims list responses to stay under its character cap (about 24,000 characters), so a page
can hold FEWER rows than `limit`; it then adds a warning `<list>: returned N of M items ...`.
`get_all` and `evidence_all` therefore advance `offset` by the number of rows received, never by
`limit`. `coverage` says whether a single-page result is complete or trimmed.

httpx is imported only by `KG` when no `fetch` is given, so the paging logic runs (and is tested)
with the standard library alone.
"""

import pathlib


class KG:
    """`KG(url, token_file)` for a live API; `KG(fetch=f)` with `f(path, params) -> (status, envelope)`."""

    def __init__(self, url=None, token_file=None, fetch=None, timeout=60):
        if fetch is None:
            import httpx

            token = pathlib.Path(token_file).read_text().strip()
            client = httpx.Client(
                base_url=url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout
            )

            def fetch(path, params):
                r = client.get(path, params=params)
                return r.status_code, r.json()

        self.fetch = fetch

    def get(self, path, **params):
        """GET one endpoint; return the envelope. Raise on status=error; print warnings."""
        status, env = self.fetch(path, params)
        if env["status"] != "ok":
            raise RuntimeError(f"{path} {status}: {env['error']}")
        for w in env["warnings"]:
            print("  warning:", w)
        return env

    def get_all(self, path, **params):
        """Every row of a list endpoint: page on with offset += len(data) until page.total."""
        rows, offset = [], params.pop("offset", 0)
        while True:
            env = self.get(path, offset=offset, **params)
            rows += env["data"]
            offset += len(env["data"])
            if not env["data"] or offset >= (env["page"]["total"] or 0):
                break
        env["data"] = rows
        env["page"] = {**env["page"], "offset": 0, "returned": len(rows)}
        env["warnings"] = [w for w in env["warnings"] if "to stay within" not in w]  # paged through
        return env

    def evidence_all(self, edge_id, **params):
        """`/evidence/{edge_id}` with every StudyResult (paged the same way)."""
        srs, offset = [], 0
        while True:
            env = self.get(f"/evidence/{edge_id}", offset=offset, **params)
            got = env["data"]["study_results"]
            srs += got
            offset += len(got)
            if not got or offset >= (env["page"]["total"] or 0):
                break
        env["data"]["study_results"] = srs
        env["page"] = {**env["page"], "offset": 0, "returned": len(srs)}
        env["warnings"] = [w for w in env["warnings"] if "data.study_results:" not in w]
        return env

    def resolve(self, q, category="biolink:Gene"):
        """search_entities, keeping only exact CURIE / symbol matches; fail loudly otherwise."""
        env = self.get("/entities/search", q=q, category=category, limit=5)
        exact = [h for h in env["data"] if h["match"] in ("exact_id", "exact_symbol")]
        if len(exact) != 1:
            raise LookupError(
                f"{q}: {len(exact)} exact matches in {env['kg_release']}: {env['data']}"
            )
        return exact[0]["id"], env


def coverage(env, rows=None):
    """'complete: n of total', 'trimmed: n of total ...' or 'partial: ...' for one response."""
    rows = env["data"] if rows is None else rows
    page = env.get("page") or {}
    total, offset, n = page.get("total"), page.get("offset", 0), len(rows)
    trim = [w for w in env.get("warnings", []) if "to stay within" in w]
    if trim:
        return f"trimmed: {n} of {total} (character cap; page on with offset={offset + n})"
    if total is None:
        return f"top {n} (ranked; total not reported)"
    if offset + n < total:
        return f"partial: {n} of {total} (limit; page on with offset={offset + n})"
    return f"complete: {n} of {total}"
