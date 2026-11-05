"""Tests of scripts/read_corpus.py with a fake model in place of Claude. Standard library only."""

import csv
import importlib.util
import json
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "read_corpus.py"
spec = importlib.util.spec_from_file_location("read_corpus", SCRIPT)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

QUESTION = "Which genes cause inherited retinal disease through haploinsufficiency?"


def passage(key, *sentences, page=1):
    pmid, chunk = key.split(":")
    return {
        "key": key,
        "pmid": pmid,
        "chunk": int(chunk),
        "page": page,
        "sentences": list(sentences),
    }


def fake_model(answers, calls):
    """A model that answers each passage from ``answers`` (key -> sentence numbers), leaving out
    the passages in ``answers["skip"]`` when it gets more than one at a time."""

    def call(messages):
        user = messages[1]["content"]
        pmids = re.findall(r"^P\d+ — PMID (\d+)", user, re.M)
        calls.append(len(pmids))
        rows = []
        for i, pmid in enumerate(pmids, 1):
            key = next(k for k in answers if k.startswith(pmid + ":"))
            if key in answers.get("skip", ()) and len(pmids) > 1:
                continue
            rows.append({"id": f"P{i}", "sentences": answers[key], "note": f"note {key}"})
        return json.dumps({"passages": rows}), {"input_tokens": 1000, "output_tokens": 100}

    return call


def test_split_sentences_keeps_abbreviations():
    text = "Smith et al. reported PAX6 loss. Fig. 2 shows it! (A) Second   line? yes."
    assert rc.split_sentences(text) == [
        "Smith et al. reported PAX6 loss.",
        "Fig. 2 shows it!",
        "(A) Second line? yes.",
    ]


def test_prompt_is_the_tested_one():
    system = rc.read_messages(QUESTION, [passage("1:0", "A.")])[0]["content"]
    assert system.startswith(
        "You read passages from research papers in the lab's RetiGene corpus (inherited retinal "
        "disease) for one question. For EACH passage, list the numbers of the sentences"
    )
    assert '{"passages": [{"id": "P1", "sentences": [3, 4], "note": "what they say' in system


def test_read_messages_numbers_sentences():
    user = rc.read_messages(QUESTION, [passage("11:3", "One.", "Two.", page=7)])[1]["content"]
    assert user == f"Question: {QUESTION}\n\nP1 — PMID 11, p. 7\n[1] One.\n[2] Two."


def test_parse_read_drops_bad_numbers_and_ids():
    batch = [passage("1:0", "a.", "b."), passage("2:0", "c.")]
    raw = '```json\n{"passages": [{"id": "P1", "sentences": [2, 9, "x", 2]}, {"id": "P7"}]}\n```'
    assert rc.parse_read(raw, batch) == {0: ([2], "")}
    assert rc.parse_read("no json here", batch) is None
    assert rc.parse_read('Here: {"passages": [{"id": "2", "sentences": []}]} done', batch) == {
        1: ([], "")
    }


def test_read_batch_asks_a_left_out_passage_alone():
    batch = [passage("1:0", "a."), passage("2:0", "b.", "c.")]
    calls = []
    got = rc.read_batch(
        fake_model({"1:0": [1], "2:0": [2], "skip": {"2:0"}}, calls), QUESTION, batch
    )
    assert calls == [2, 1]
    assert got["results"] == {
        "1:0": {"sentences": [1], "note": "note 1:0"},
        "2:0": {"sentences": [2], "note": "note 2:0"},
    }
    assert got["failed"] == []
    assert len(got["usage"]) == 2


def test_read_batch_reports_failures():
    def broken(messages):
        raise RuntimeError("overloaded")

    got = rc.read_batch(broken, QUESTION, [passage("1:0", "a."), passage("2:0", "b.")])
    assert got["results"] == {}
    assert got["failed"] == ["1:0", "2:0"]


def test_read_resumes_and_writes_outputs(tmp_path):
    ps = [passage(f"{i}:0", f"Gene {i} first.", f"Gene {i} second.") for i in range(1, 8)]
    answers = {p["key"]: ([2] if int(p["pmid"]) % 2 else []) for p in ps}
    calls = []
    out = tmp_path / "read"
    first = rc.read_corpus(fake_model(answers, calls), QUESTION, ps[:4], out, batch=3, workers=2)
    assert sorted(first["results"]) == ["1:0", "2:0", "3:0", "4:0"]
    calls.clear()
    run = rc.read_corpus(fake_model(answers, calls), QUESTION, ps, out, batch=3, workers=2)
    assert sum(calls) == 3  # only the three passages the first run did not read
    assert run["usage"]["calls"] == 3  # two batches before, one now
    settings = {"price_in": 0.1, "price_out": 0.5, "model": "fake"}
    summary = rc.write_outputs(out, QUESTION, ps, run, {"1": {"citation": "Doe 2020"}}, settings)
    assert (summary["read"], summary["bearing"], summary["papers"]) == (7, 4, 4)
    with (out / "evidence.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert [r["pmid"] for r in rows] == ["1", "3", "5", "7"]
    assert rows[0]["sentences"] == "Gene 1 second."
    assert rows[0]["citation"] == "Doe 2020"
    assert rows[1]["citation"] == "PMID 3"
    with (out / "read_log.csv").open() as fh:
        status = {r["pmid"]: r["status"] for r in csv.DictReader(fh)}
    assert status == {"1": "bears", "2": "read", "3": "bears", "4": "read", "5": "bears",
                      "6": "read", "7": "bears"}  # fmt: skip
    usage = json.loads((out / "usage.json").read_text())
    assert usage["usage"]["cost_usd"] == pytest.approx(3 * (1000 * 0.1 + 100 * 0.5) / 1e6, abs=1e-4)


def test_read_refuses_another_question_in_the_same_folder(tmp_path):
    ps = [passage("1:0", "a.")]
    rc.read_corpus(fake_model({"1:0": []}, []), QUESTION, ps, tmp_path)
    with pytest.raises(SystemExit):
        rc.read_corpus(fake_model({"1:0": []}, []), "Another question?", ps, tmp_path)


def test_estimate_counts_calls_and_ranges():
    ps = [passage(f"{i}:0", "x" * 360) for i in range(25)]
    est = rc.estimate(ps, QUESTION, batch=10, workers=5)
    assert est["calls"] == 3
    lo, hi = est["cost_usd"]
    assert 0 < lo < hi
    assert est["output_tokens"] == [25 * rc.OUT_PER_PASSAGE[0], 25 * rc.OUT_PER_PASSAGE[1]]


def write_hgnc(path):
    rows = [
        ("UNC119", "HRG4", "", "Approved"),
        ("PAX6", "AN|AN2|MIM", "", "Approved"),
        ("BMP4", "", "BMP2B", "Approved"),
        ("GENEA", "SHARED1", "", "Approved"),
        ("GENEB", "SHARED1", "", "Approved"),
        ("OLD1", "", "", "Entry Withdrawn"),
    ]
    with path.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["symbol", "alias_symbol", "prev_symbol", "status"])
        w.writerows(rows)


def test_gene_table_maps_aliases_and_skips_field_words(tmp_path):
    hgnc = tmp_path / "hgnc.tsv"
    write_hgnc(hgnc)
    symbols = rc.hgnc_symbols(hgnc)
    assert symbols["HRG4"] == "UNC119"
    assert "SHARED1" not in symbols  # an alias of two genes names neither
    assert symbols["AN2"] == "PAX6"
    assert "AN" not in symbols  # too short
    assert "MIM" not in symbols  # no digit: "MIM 123456" is an OMIM number, not a gene
    assert "OLD1" not in symbols
    evidence = tmp_path / "evidence.csv"
    with evidence.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(rc.EVIDENCE_COLUMNS)
        w.writerow(
            ["10", 0, 1, "", "", "", "1", "HRG4 loss in the RPE. PAX6 is dosage-sensitive.", ""]
        )
        w.writerow(["11", 2, 3, "", "", "", "4", "Heterozygous PAX6 and BMP2B variants.", ""])
        w.writerow(["11", 5, 6, "", "", "", "2", "PAX6 again, SHARED1 too, see MIM 607108.", ""])
    rows = rc.gene_table(evidence, symbols)
    assert [r["gene"] for r in rows] == ["PAX6", "BMP4", "UNC119"]
    pax6 = rows[0]
    assert (pax6["papers"], pax6["passages"], pax6["pmids"]) == (2, 3, "10 11")
    assert pax6["example"] == "PMID 10: PAX6 is dosage-sensitive."
    assert rows[1]["written_as"] == "BMP2B"


def test_genes_command(tmp_path, capsys):
    hgnc = tmp_path / "hgnc.tsv"
    write_hgnc(hgnc)
    evidence = tmp_path / "evidence.csv"
    with evidence.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(rc.EVIDENCE_COLUMNS)
        w.writerow(["10", 0, 1, "", "", "", "1", "PAX6 haploinsufficiency.", ""])
    assert (
        rc.main(["genes", "--evidence", str(evidence), "--hgnc", str(hgnc), "--check", "PAX6,BMP4"])
        == 0
    )
    printed = capsys.readouterr().out
    assert "1 genes" in printed
    assert "PAX6: 1 papers, 1 passages" in printed
    assert "BMP4: absent" in printed
    assert (tmp_path / "genes.csv").is_file()


def test_load_passages_skips_empty_and_repeated(tmp_path):
    chunks = tmp_path / "chunks.jsonl"
    rows = [
        {"pmid": "1", "chunk": 0, "page": 1, "text": "A b. C d."},
        {"pmid": "1", "chunk": 0, "page": 1, "text": "repeat"},
        {"pmid": "2", "chunk": 0, "page": 1, "text": "   "},
        {"pmid": "3", "chunk": 4, "page": None, "text": "E."},
    ]
    chunks.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    ps = rc.load_passages(chunks)
    assert [p["key"] for p in ps] == ["1:0", "3:4"]
    assert ps[0]["sentences"] == ["A b.", "C d."]
